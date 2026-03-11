def read_temperature_and_voltage(self):
        with self.serial_port_ctrl_lock:
            resp = self._request(2, None)
            if resp is None or resp.error != 0:
                raise Exception("failed reading status!")

            status = coms_pb2.QState()
#            status.ParseFromString(resp.data[1:])
            status.ParseFromString(resp.data[0:])

            return {
                "temp": [status.temp1 * 0.0625, status.temp2 * 0.0625, None, None],
                "voltage": [(status.sys_voltages & 0xffff) / 1000.0, ((status.sys_voltages >> 16) & 0xffff) / 1000.0, None, None],
                "hb1_temps": [
                    status.hb1_temp_pair1 & 0xffff, ((status.hb1_temp_pair1 >> 16) & 0xffff), 
                    status.hb1_temp_pair2 & 0xffff, ((status.hb1_temp_pair2 >> 16) & 0xffff), 
                    status.hb1_temp_pair3 & 0xffff, ((status.hb1_temp_pair3 >> 16) & 0xffff), 
                    status.hb1_temp_pair4 & 0xffff, ((status.hb1_temp_pair4 >> 16) & 0xffff)],
                "hb2_temps": [
                    status.hb2_temp_pair1 & 0xffff, ((status.hb2_temp_pair1 >> 16) & 0xffff), 
                    status.hb2_temp_pair2 & 0xffff, ((status.hb2_temp_pair2 >> 16) & 0xffff), 
                    status.hb2_temp_pair3 & 0xffff, ((status.hb2_temp_pair3 >> 16) & 0xffff), 
                    status.hb2_temp_pair4 & 0xffff, ((status.hb2_temp_pair4 >> 16) & 0xffff)],

            }