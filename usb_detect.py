"""
usb_detect.py
=============
Auto-detect COM ports / TTY devices for a USB composite device by VID/PID.

Tested platforms: Linux (pyudev), Windows (SetupAPI + winreg via ctypes).

Usage
-----
    from usb_detect import find_devices, DeviceInterfaces

    devices = find_devices()          # uses default VID=0xCAFE, PID=0x4003
    for dev in devices:
        print(dev)
        print(f"  IF0 → {dev.interface_0.port}")
        print(f"  IF1 → {dev.interface_1.port}")
        print(f"  IF2 → {dev.interface_2.port}")

    # Custom VID/PID
    devices = find_devices(vid=0x1234, pid=0x5678)

Dataclasses
-----------
    UsbInterface   – one ACM/COM port (port, interface number, name)
    DeviceInterfaces – groups the three interfaces for a single physical device
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from typing import List, Optional

# ---------------------------------------------------------------------------
# Default target device
# ---------------------------------------------------------------------------
DEFAULT_VID = 0xCAFE
DEFAULT_PID = 0x4003

# Expected number of CDC interfaces per device
IFACE_COUNT = 3


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class UsbInterface:
    """Represents one CDC ACM interface / COM port."""
    port: str                        # e.g. '/dev/ttyACM0' or 'COM3'
    interface: int                   # bInterfaceNumber (MI_xx on Windows)
    name: str = "(not provided)"     # iInterface string descriptor or friendly name
    bus_desc: str = ""               # bus-reported device description (iProduct/iInterface)
    device_id: str = ""              # raw sysfs path or Windows DeviceInstanceID

    def __repr__(self) -> str:
        return (
            f"UsbInterface(interface={self.interface}, port={self.port!r}, "
            f"name={self.name!r}, bus_desc={self.bus_desc!r})"
        )


@dataclass
class DeviceInterfaces:
    """
    Groups all CDC interfaces of one physical USB device.

    Attributes
    ----------
    vid, pid        : USB vendor / product IDs
    serial          : USB serial number string (if available)
    interface_0     : first interface  (lowest bInterfaceNumber)
    interface_1     : second interface
    interface_2     : third interface
    extra           : any additional interfaces beyond the expected three
    """
    vid: int
    pid: int
    serial: str = ""
    interface_0: Optional[UsbInterface] = None
    interface_1: Optional[UsbInterface] = None
    interface_2: Optional[UsbInterface] = None
    extra: List[UsbInterface] = field(default_factory=list)

    # ------------------------------------------------------------------ #
    def all_interfaces(self) -> List[UsbInterface]:
        """Return all interfaces in ascending interface-number order."""
        base = [self.interface_0, self.interface_1, self.interface_2]
        return [i for i in base if i is not None] + self.extra

    def as_dict(self) -> dict:
        return {
            "vid": f"0x{self.vid:04X}",
            "pid": f"0x{self.pid:04X}",
            "serial": self.serial,
            "interfaces": [
                {"interface": i.interface, "port": i.port, "name": i.name, "bus_desc": i.bus_desc}
                for i in self.all_interfaces()
            ],
        }

    def __repr__(self) -> str:
        ifaces = ", ".join(
            f"IF{i.interface}={i.port!r}" for i in self.all_interfaces()
        )
        return (
            f"DeviceInterfaces(VID=0x{self.vid:04X}, PID=0x{self.pid:04X}, "
            f"serial={self.serial!r}, [{ifaces}])"
        )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _build_device_interfaces(
    vid: int, pid: int, iface_list: List[UsbInterface], serial: str = ""
) -> DeviceInterfaces:
    """Pack a sorted list of UsbInterface objects into a DeviceInterfaces."""
    sorted_ifaces = sorted(iface_list, key=lambda x: x.interface)
    dev = DeviceInterfaces(vid=vid, pid=pid, serial=serial)
    slots = ["interface_0", "interface_1", "interface_2"]
    for idx, iface in enumerate(sorted_ifaces):
        if idx < len(slots):
            setattr(dev, slots[idx], iface)
        else:
            dev.extra.append(iface)
    return dev


# ---------------------------------------------------------------------------
# Linux backend  (pyudev)
# ---------------------------------------------------------------------------

def _find_linux(vid: int, pid: int) -> List[DeviceInterfaces]:
    try:
        import pyudev  # type: ignore
    except ImportError as exc:
        raise ImportError(
            "pyudev is required on Linux. Install with: pip install pyudev"
        ) from exc

    context = pyudev.Context()
    # key: usb_device syspath → list of UsbInterface
    grouped: dict[str, list[UsbInterface]] = {}
    serials: dict[str, str] = {}

    for device in context.list_devices(subsystem="tty"):
        if "ttyACM" not in (device.sys_name or ""):
            continue

        usb_iface = device.find_parent(subsystem="usb", device_type="usb_interface")
        if usb_iface is None:
            continue

        usb_dev = device.find_parent(subsystem="usb", device_type="usb_device")
        if usb_dev is None:
            continue

        try:
            dev_vid = int(usb_dev.attributes.asstring("idVendor"), 16)
            dev_pid = int(usb_dev.attributes.asstring("idProduct"), 16)
        except Exception:
            continue

        if dev_vid != vid or dev_pid != pid:
            continue

        # bInterfaceNumber is the last numeric component of the interface sysname
        # e.g. "1-1.2:1.2"  →  2
        try:
            iface_num = int(usb_iface.sys_name.split(".")[-1])
        except (ValueError, IndexError):
            iface_num = -1

        # iInterface string descriptor (may be absent)
        try:
            iface_name = usb_iface.attributes.asstring("interface")
        except Exception:
            iface_name = "(not provided)"

        # USB serial number
        try:
            serial = usb_dev.attributes.asstring("serial")
        except Exception:
            serial = ""

        dev_path = usb_dev.sys_path
        serials[dev_path] = serial
        grouped.setdefault(dev_path, []).append(
            UsbInterface(
                port=f"/dev/{device.sys_name}",
                interface=iface_num,
                name=iface_name,
                device_id=usb_iface.sys_path,
            )
        )

    return [
        _build_device_interfaces(vid, pid, ifaces, serials.get(dev_path, ""))
        for dev_path, ifaces in grouped.items()
    ]


# ---------------------------------------------------------------------------
# Windows backend  (SetupAPI via ctypes + winreg)
# ---------------------------------------------------------------------------

def _debug_windows_list_all_com_ports() -> None:
    """
    Debug helper — prints every COM-port device instance ID that SetupAPI
    can see, regardless of VID/PID. Run this to check what strings are
    actually present so you can verify the VID/PID filter.

    Call directly:
        from usb_detect import _debug_windows_list_all_com_ports
        _debug_windows_list_all_com_ports()
    """
    import ctypes
    import ctypes.wintypes as wintypes

    setupapi = ctypes.windll.setupapi
    kernel32 = ctypes.windll.kernel32

    DIGCF_PRESENT         = 0x02
    DIGCF_DEVICEINTERFACE = 0x10
    ERROR_NO_MORE_ITEMS   = 259
    INVALID_HANDLE        = wintypes.HANDLE(-1).value

    _GUID_BYTES = bytes([
        0xE0, 0xD1, 0xE0, 0x86, 0x89, 0x80, 0xD0, 0x11,
        0x9C, 0xE4, 0x08, 0x00, 0x3E, 0x30, 0x1F, 0x73,
    ])
    guid_bytes = (ctypes.c_byte * 16)(*_GUID_BYTES)

    class SP_DEVINFO_DATA(ctypes.Structure):
        _fields_ = [
            ("cbSize",    wintypes.DWORD),
            ("ClassGuid", ctypes.c_byte * 16),
            ("DevInst",   wintypes.DWORD),
            ("Reserved",  ctypes.POINTER(ctypes.c_ulong)),
        ]

    hdevinfo = setupapi.SetupDiGetClassDevsW(
        ctypes.byref(guid_bytes), None, None,
        DIGCF_PRESENT | DIGCF_DEVICEINTERFACE,
    )
    if hdevinfo == INVALID_HANDLE:
        print("[debug] SetupDiGetClassDevsW failed")
        return

    try:
        devinfo_data = SP_DEVINFO_DATA()
        devinfo_data.cbSize = ctypes.sizeof(SP_DEVINFO_DATA)
        index = 0
        print("[debug] All COM-port device instance IDs visible to SetupAPI:")
        while True:
            ok = setupapi.SetupDiEnumDeviceInfo(hdevinfo, index, ctypes.byref(devinfo_data))
            if not ok:
                if kernel32.GetLastError() == ERROR_NO_MORE_ITEMS:
                    break
                index += 1
                continue
            buf = ctypes.create_unicode_buffer(512)
            if setupapi.SetupDiGetDeviceInstanceIdW(
                hdevinfo, ctypes.byref(devinfo_data), buf, ctypes.sizeof(buf), None
            ):
                print(f"  [{index:3d}] {buf.value}")
            index += 1
    finally:
        setupapi.SetupDiDestroyDeviceInfoList(hdevinfo)


def _find_windows(vid: int, pid: int) -> List[DeviceInterfaces]:
    import ctypes
    import ctypes.wintypes as wintypes
    import winreg  # stdlib on Windows

    # GUID_DEVCLASS_PORTS = {4D36E978-E325-11CE-BFC1-08002BE10318}
    # Device *setup class* GUID for "Ports (COM & LPT)".
    # Use this (without DIGCF_DEVICEINTERFACE) instead of GUID_DEVINTERFACE_COMPORT
    # because many USB CDC ACM drivers do not register the device interface GUID,
    # so SetupDiGetClassDevsW with DIGCF_DEVICEINTERFACE misses them.
    # Stored in little-endian mixed-endian layout as Windows GUID struct:
    #   Data1 (4B LE), Data2 (2B LE), Data3 (2B LE), Data4 (8B BE)
    _GUID_BYTES = bytes([
        0x78, 0xE9, 0x36, 0x4D,  # Data1 = 4D36E978 (LE)
        0x25, 0xE3,              # Data2 = E325     (LE)
        0xCE, 0x11,              # Data3 = 11CE     (LE)
        0xBF, 0xC1,              # Data4[0:2]
        0x08, 0x00, 0x2B, 0xE1, 0x03, 0x18,  # Data4[2:8]
    ])
    _guid_bytes = (ctypes.c_byte * 16)(*_GUID_BYTES)

    setupapi  = ctypes.windll.setupapi
    kernel32  = ctypes.windll.kernel32
    advapi32  = ctypes.windll.advapi32

    # On 64-bit Windows ctypes defaults return types to c_int (32-bit), which
    # truncates pointer-sized handles.  Set restype explicitly on all functions
    # that return handles or pointers.
    setupapi.SetupDiGetClassDevsW.restype              = ctypes.c_void_p
    setupapi.SetupDiOpenDevRegKey.restype              = ctypes.c_void_p
    setupapi.SetupDiEnumDeviceInfo.restype             = wintypes.BOOL
    setupapi.SetupDiGetDeviceInstanceIdW.restype       = wintypes.BOOL
    setupapi.SetupDiGetDeviceRegistryPropertyW.restype = wintypes.BOOL
    setupapi.SetupDiDestroyDeviceInfoList.restype      = wintypes.BOOL
    setupapi.SetupDiGetDevicePropertyW.restype         = wintypes.BOOL

    cfgmgr = ctypes.windll.CfgMgr32
    cfgmgr.CM_Get_Parent.restype     = wintypes.DWORD
    cfgmgr.CM_Get_Device_IDW.restype = wintypes.DWORD

    DIGCF_PRESENT         = 0x02
    SPDRP_FRIENDLYNAME    = 0x0C
    SPDRP_DEVICEDESC      = 0x00
    ERROR_NO_MORE_ITEMS   = 259
    KEY_READ              = 0x20019
    DICS_FLAG_GLOBAL      = 0x00000001
    DIREG_DEV             = 0x00000001
    INVALID_HANDLE        = ctypes.c_void_p(-1).value  # platform-correct INVALID_HANDLE_VALUE

    class SP_DEVINFO_DATA(ctypes.Structure):
        _fields_ = [
            ("cbSize",    wintypes.DWORD),
            ("ClassGuid", ctypes.c_byte * 16),
            ("DevInst",   wintypes.DWORD),
            ("Reserved",  ctypes.POINTER(ctypes.c_ulong)),
        ]

    def get_registry_property(hdevinfo, devinfo_data, prop_id) -> Optional[str]:
        buf  = ctypes.create_unicode_buffer(512)
        size = wintypes.DWORD(ctypes.sizeof(buf))
        ok   = setupapi.SetupDiGetDeviceRegistryPropertyW(
            hdevinfo, ctypes.byref(devinfo_data), prop_id,
            None,
            ctypes.cast(buf, ctypes.POINTER(ctypes.c_byte)),
            size, ctypes.byref(size),
        )
        return buf.value if ok else None

    def get_instance_id(hdevinfo, devinfo_data) -> Optional[str]:
        buf = ctypes.create_unicode_buffer(512)
        ok  = setupapi.SetupDiGetDeviceInstanceIdW(
            hdevinfo, ctypes.byref(devinfo_data),
            buf, ctypes.sizeof(buf), None,
        )
        return buf.value if ok else None

    def get_com_port(hdevinfo, devinfo_data) -> Optional[str]:
        """Read PortName directly from the device's registry key."""
        hkey_raw = setupapi.SetupDiOpenDevRegKey(
            hdevinfo, ctypes.byref(devinfo_data),
            DICS_FLAG_GLOBAL, 0, DIREG_DEV, KEY_READ,
        )
        if hkey_raw == INVALID_HANDLE or hkey_raw is None:
            return None
        hkey = ctypes.c_void_p(hkey_raw)
        try:
            buf  = ctypes.create_unicode_buffer(256)
            size = wintypes.DWORD(ctypes.sizeof(buf))
            ret  = advapi32.RegQueryValueExW(
                hkey, "PortName", None, None,
                ctypes.cast(buf, ctypes.POINTER(ctypes.c_byte)),
                ctypes.byref(size),
            )
            return buf.value if ret == 0 else None
        finally:
            advapi32.RegCloseKey(hkey)

    # DEVPKEY_Device_BusReportedDeviceDesc = {540b947e-8b40-45bc-a8a2-6a0b894cbda2}, 4
    _DEVPKEY_BUS_DESC_GUID = (ctypes.c_byte * 16)(
        0x7e, 0x94, 0x0b, 0x54,  # Data1 = 540b947e (LE)
        0x40, 0x8b,              # Data2 = 8b40     (LE)
        0xbc, 0x45,              # Data3 = 45bc     (LE)
        0xa8, 0xa2, 0x6a, 0x0b, 0x89, 0x4c, 0xbd, 0xa2,  # Data4
    )

    class DEVPROPKEY(ctypes.Structure):
        _fields_ = [("fmtid", ctypes.c_byte * 16), ("pid", wintypes.ULONG)]

    _devpkey_bus_desc = DEVPROPKEY(fmtid=_DEVPKEY_BUS_DESC_GUID, pid=4)

    def get_bus_desc(hdevinfo, devinfo_data) -> str:
        """Return the bus-reported device description (DEVPKEY_Device_BusReportedDeviceDesc)."""
        buf      = ctypes.create_unicode_buffer(512)
        prop_type = wintypes.ULONG(0)
        req_size  = wintypes.DWORD(0)
        ok = setupapi.SetupDiGetDevicePropertyW(
            hdevinfo, ctypes.byref(devinfo_data),
            ctypes.byref(_devpkey_bus_desc),
            ctypes.byref(prop_type),
            ctypes.cast(buf, ctypes.POINTER(ctypes.c_byte)),
            ctypes.sizeof(buf),
            ctypes.byref(req_size),
            0,
        )
        return buf.value if ok else ""

    def get_parent_serial(devinst: int) -> str:
        """
        Walk up to the parent USB composite device via CM_Get_Parent and extract
        the USB serial number from its device instance ID.
        e.g. parent ID "USB\\VID_CAFE&PID_4003\\0123456789ABCDEF"  →  "0123456789ABCDEF"
        Returns "" if the parent has no real serial (only a location string).
        """
        CR_SUCCESS = 0
        parent_inst = wintypes.DWORD(0)
        if cfgmgr.CM_Get_Parent(ctypes.byref(parent_inst), devinst, 0) != CR_SUCCESS:
            return ""
        buf = ctypes.create_unicode_buffer(512)
        if cfgmgr.CM_Get_Device_IDW(parent_inst, buf, ctypes.sizeof(buf), 0) != CR_SUCCESS:
            return ""
        parts = buf.value.split("\\")
        last  = parts[-1] if parts else ""
        # Real USB serials are plain alphanumeric strings.
        # Location strings contain "&" (e.g. "8&155004EE&2").  Reject those.
        if "&" in last or not last:
            return ""
        return last

    vid_str = f"VID_{vid:04X}"
    pid_str = f"PID_{pid:04X}"

    hdevinfo = setupapi.SetupDiGetClassDevsW(
        ctypes.byref(_guid_bytes),
        None, None,
        DIGCF_PRESENT,  # no DIGCF_DEVICEINTERFACE — this is a class GUID, not an interface GUID
    )
    if hdevinfo == INVALID_HANDLE or hdevinfo is None:
        raise ctypes.WinError()
    # Wrap as c_void_p so ctypes passes it correctly as a 64-bit handle
    hdevinfo = ctypes.c_void_p(hdevinfo)

    # key: (vid, pid, parent_prefix)  →  list[UsbInterface]
    # We group by the device path up to (but not including) the MI_xx part.
    grouped: dict[str, list[UsbInterface]] = {}
    serials: dict[str, str] = {}

    try:
        devinfo_data      = SP_DEVINFO_DATA()
        devinfo_data.cbSize = ctypes.sizeof(SP_DEVINFO_DATA)
        index = 0

        while True:
            ok = setupapi.SetupDiEnumDeviceInfo(
                hdevinfo, index, ctypes.byref(devinfo_data)
            )
            index += 1
            if not ok:
                if kernel32.GetLastError() == ERROR_NO_MORE_ITEMS:
                    break
                continue

            device_id = get_instance_id(hdevinfo, devinfo_data) or ""
            upper     = device_id.upper()

            if vid_str not in upper or pid_str not in upper:
                continue

            mi_match  = re.search(r"MI_(\d+)", upper)
            iface_num = int(mi_match.group(1)) if mi_match else -1

            com_port  = get_com_port(hdevinfo, devinfo_data)
            if not com_port:
                continue   # not a COM port node

            friendly  = get_registry_property(hdevinfo, devinfo_data, SPDRP_FRIENDLYNAME)
            desc      = get_registry_property(hdevinfo, devinfo_data, SPDRP_DEVICEDESC)
            name      = friendly or desc or "(not provided)"

            # Group key: VID/PID prefix only, stripping &MI_nn and the trailing
            # instance component.  e.g. "USB\VID_CAFE&PID_4003&MI_02\8&xxx&0002"
            # becomes "USB\VID_CAFE&PID_4003"
            group_key = re.sub(r"&MI_\d+\\.*$", "", device_id, flags=re.IGNORECASE)
            serial    = get_parent_serial(devinfo_data.DevInst)
            serials[group_key] = serial

            grouped.setdefault(group_key, []).append(
                UsbInterface(
                    port=com_port,
                    interface=iface_num,
                    name=name,
                    bus_desc=get_bus_desc(hdevinfo, devinfo_data),
                    device_id=device_id,
                )
            )
    finally:
        setupapi.SetupDiDestroyDeviceInfoList(hdevinfo)

    return [
        _build_device_interfaces(vid, pid, ifaces, serials.get(gk, ""))
        for gk, ifaces in grouped.items()
    ]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def find_devices(
    vid: int = DEFAULT_VID,
    pid: int = DEFAULT_PID,
) -> List[DeviceInterfaces]:
    """
    Scan the system for USB devices matching *vid* / *pid* and return a list
    of :class:`DeviceInterfaces` — one entry per physical device found.

    Each :class:`DeviceInterfaces` object has:
      - ``interface_0`` / ``interface_1`` / ``interface_2`` – the three CDC
        ACM ports in ascending interface-number order
      - ``all_interfaces()`` – flat sorted list
      - ``as_dict()``        – JSON-friendly dict

    Parameters
    ----------
    vid : int
        USB Vendor ID  (default 0xCAFE)
    pid : int
        USB Product ID (default 0x4003)

    Returns
    -------
    List[DeviceInterfaces]
        Empty list if no matching device is found.

    Raises
    ------
    NotImplementedError
        If the current platform is not Linux or Windows.
    ImportError
        If required platform libraries are not installed.
    """
    if sys.platform.startswith("linux"):
        return _find_linux(vid, pid)
    elif sys.platform == "win32":
        return _find_windows(vid, pid)
    else:
        raise NotImplementedError(
            f"Platform {sys.platform!r} is not supported. "
            "Supported: 'linux', 'win32'."
        )


# ---------------------------------------------------------------------------
# CLI  (python usb_detect.py)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse, json

    parser = argparse.ArgumentParser(
        description="Detect USB CDC ACM / COM ports by VID and PID."
    )
    parser.add_argument("--vid", type=lambda x: int(x, 0), default=DEFAULT_VID,
                        help=f"USB Vendor ID  (default 0x{DEFAULT_VID:04X})")
    parser.add_argument("--pid", type=lambda x: int(x, 0), default=DEFAULT_PID,
                        help=f"USB Product ID (default 0x{DEFAULT_PID:04X})")
    parser.add_argument("--json", action="store_true",
                        help="Output as JSON")
    parser.add_argument("--debug", action="store_true",
                        help="(Windows) Dump all COM device IDs seen by SetupAPI")
    args = parser.parse_args()

    if args.debug:
        if sys.platform == "win32":
            _debug_windows_list_all_com_ports()
        else:
            print("--debug is only supported on Windows")
        sys.exit(0)

    devices = find_devices(vid=args.vid, pid=args.pid)

    if not devices:
        print(f"No devices found for VID=0x{args.vid:04X} PID=0x{args.pid:04X}")
        sys.exit(1)

    if args.json:
        print(json.dumps([d.as_dict() for d in devices], indent=2))
    else:
        for i, dev in enumerate(devices):
            print(f"Device #{i}  VID=0x{dev.vid:04X}  PID=0x{dev.pid:04X}"
                  + (f"  serial={dev.serial}" if dev.serial else ""))
            for iface in dev.all_interfaces():
                bus = f"  [{iface.bus_desc}]" if iface.bus_desc else ""
                print(f"  Interface {iface.interface:2d}  {iface.port:<15s}  {iface.name}{bus}")
        print()
