CENTURY = 20

BIT_MEANINGS = {
    0 : "start-bit",
    1 : "weather-info-1",          # weather info bit (encrypted)
    2 : "weather-info-2",          # weather info bit (encrypted)
    3 : "weather-info-3",          # weather info bit (encrypted)
    4 : "weather-info-4",          # weather info bit (encrypted)
    5 : "weather-info-5",          # weather info bit (encrypted)
    6 : "weather-info-6",          # weather info bit (encrypted)
    7 : "weather-info-7",          # weather info bit (encrypted)
    8 : "weather-info-8",          # weather info bit (encrypted)
    9 : "weather-info-9",          # weather info bit (encrypted)
    10 : "weather-info-10",        # weather info bit (encrypted)
    11 : "weather-info-11",        # weather info bit (encrypted)
    12 : "weather-info-12",        # weather info bit (encrypted)
    13 : "weather-info-13",        # weather info bit (encrypted)
    14 : "weather-info-14",        # weather info bit (encrypted)
    15 : "call-bit",               # abnormal transmitter operation of the dcf-77 antenna
    16 : "summer-time-notice",
    17 : "summer-time-1",          # „01“: MEZ
    18 : "summer-time-2",          # „10“: MESZ
    19 : "leap-second",            # Leap second accouncement. Set during hour before leap second
    20 : "time-begin",             # 1
    21 : "minute-one-1",           # Time encoded in BCD
    22 : "minute-one-2",
    23 : "minute-one-4",
    24 : "minute-one-8",
    25 : "minute-tens-10",
    26 : "minute-tens-20",
    27 : "minute-tens-40",
    28 : "minute-parity",          # must be even over minute bits 21 - 28
    29 : "hour-one-1",
    30 : "hour-one-2",
    31 : "hour-one-4",
    32 : "hour-one-8",
    33 : "hour-tens-10",
    34 : "hour-tens-20",
    35 : "hour-parity",            # must be even over hour bits 29-35
    36 : "calendar-day-one-1",
    37 : "calendar-day-one-2",
    38 : "calendar-day-one-4",
    39 : "calendar-day-one-8",
    40 : "calendar-day-tens-10",
    41 : "calendar-day-tens-20",
    42 : "weekday-1",
    43 : "weekday-2",
    44 : "weekday-4",
    45 : "month-number-one-1",
    46 : "month-number-one-2",
    47 : "month-number-one-4",
    48 : "month-number-one-8",
    49 : "month-number-tens-10",
    50 : "year-one-1",
    51 : "year-one-2",
    52 : "year-one-4",
    53 : "year-one-8",
    54 : "year-tens-10",
    55 : "year-tens-20",
    56 : "year-tens-40",
    57 : "year-tens-80",
    58 : "date-parity"             # must be even over date bits 36 - 58
}

LOGICAL_ERROR = 220
LOGICAL_1 = 200
LOGICAL_0 = 100


class StartBitError(Exception):
    """Raised when the startbit cannot be found"""


class LogicDurationError(Exception):
    """Raises when the duration of a logical value is too long"""


class RecordLengthError(Exception):
    """Raises when a record from a minute is too short or too long"""


class ParityError(Exception):
    """Raises when a calculated parity-value is not even"""


class TimeSyncError(Exception):
    """Raises when it is unimpossible to receive the time-signal"""

class DeviceConnectionError(Exception):
    """Raises when the device is not connected"""

class DCF_77:
    def __init__(self, pin, signal_timer, total_timer, logger, rtc, max_attempts=3):
        self.pin = pin
        self.signal_timer = signal_timer
        self.total_timer = total_timer
        self.log = logger
        self.rtc = rtc
        self.max_attempts = max_attempts
        self.attempts = 1
        self.search_ms = 60000
        self.minute_mark = 1500
        self.data_package = {}
        self.bit_num = 0
        self.success = False
        self.datetime = {}
        

    def _find_start_bit(self):
        self.log.debug("Search Start Bit")
        self.total_timer.start()
        while True:
            if not self.pin.value():
                self.signal_timer.start()
                while True:
                    total_time_passed = self.total_timer.time_since_start()
                    if self.pin.value():
                        self.signal_timer.stop()
                        time_passed = self.signal_timer.time_passed()    
                        debug_str = "low duration: " +  str(time_passed) + " ms"
                        self.log.debug(debug_str)
                        debug_str = "total search time: " +  str(total_time_passed) + " ms"
                        self.log.debug(debug_str)
                        if time_passed > self.minute_mark:
                            self.log.debug("Found start bit")
                            return True
                        break
                    if total_time_passed > self.search_ms:
                        raise StartBitError
                        

    def _measure_low_duration(self):
        self.signal_timer.start()
        while True:
            if self.pin.value():
                self.signal_timer.stop()
                time_passed = self.signal_timer.time_passed()
                debug_str = "low duration: " + str(time_passed) + " ms"
                self.log.debug(debug_str)

                return time_passed

    def _get_logic_value(self, time_passed):
        if time_passed > LOGICAL_ERROR:
            debug_str = "bit num: " + str(self.bit_num)  + " | high duration: " +  str(time_passed) + " ms | value: ?"
            self.log.debug(debug_str)
            raise LogicDurationError
        if time_passed >= LOGICAL_1:
            debug_str = "bit num: " + str(self.bit_num)  + " | high duration: " +  str(time_passed) + " ms | value: 1"
            self.log.debug(debug_str)
            return 1
        if time_passed >= LOGICAL_0:
            debug_str = "bit num: " + str(self.bit_num)  + " | high duration: " +  str(time_passed) + " ms | value: 0"
            self.log.debug(debug_str)
            return 0

    def _receive_data(self):
        self.log.debug("Receive bit encoded data")
        self.bit_num = 0
        while True:
            if self.pin.value():
                self.signal_timer.start()
                while True:
                    if not self.pin.value():
                        self.signal_timer.stop()
                        time_passed = self.signal_timer.time_passed()
                        logic_value = self._get_logic_value(time_passed)
                        self.data_package[BIT_MEANINGS[self.bit_num]] = logic_value
                        self.bit_num = self.bit_num + 1
                        if self.bit_num > len(BIT_MEANINGS):
                            raise RecordLengthError
                        break

            if self._measure_low_duration() >= self.minute_mark:
                self.bit_num = 0
                if len(self.data_package) != len(BIT_MEANINGS):
                    raise RecordLengthError
                self.log.debug("Record from one minute complete")
                self.log.debug(self.data_package)
                return self.data_package

    def _check_minute(self):
        ones = []
        if self.data_package["minute-one-1"]:
            ones.append(1)
        if self.data_package["minute-one-2"]:
            ones.append(1)
        if self.data_package["minute-one-4"]:
            ones.append(1)
        if self.data_package["minute-one-8"]:
            ones.append(1)
        if self.data_package["minute-tens-10"]:
            ones.append(1)
        if self.data_package["minute-tens-20"]:
            ones.append(1)
        if self.data_package["minute-tens-40"]:
            ones.append(1)
        if self.data_package["minute-parity"]:
            ones.append(1)

        if len(ones) % 2  != 0:
            raise ParityError('minute data')

    def _check_hour(self):
        ones = []
        if self.data_package["hour-one-1"]:
            ones.append(1)
        if self.data_package["hour-one-2"]:
            ones.append(1)
        if self.data_package["hour-one-4"]:
            ones.append(1)
        if self.data_package["hour-one-8"]:
            ones.append(1)
        if self.data_package["hour-tens-10"]:
            ones.append(1)
        if self.data_package["hour-tens-20"]:
            ones.append(1)
        if self.data_package["hour-parity"]:
            ones.append(1)

        if len(ones) % 2  != 0:
            raise ParityError('hour data')

    def _check_date(self):
        ones = []
        if self.data_package["calendar-day-one-1"]:
            ones.append(1)
        if self.data_package["calendar-day-one-2"]:
            ones.append(1)
        if self.data_package["calendar-day-one-4"]:
            ones.append(1)
        if self.data_package["calendar-day-one-8"]:
            ones.append(1)
        if self.data_package["calendar-day-tens-10"]:
            ones.append(1)
        if self.data_package["calendar-day-tens-20"]:
            ones.append(1)
        if self.data_package["weekday-1"]:
            ones.append(1)
        if self.data_package["weekday-2"]:
            ones.append(1)
        if self.data_package["weekday-4"]:
            ones.append(1)
        if self.data_package["month-number-one-1"]:
            ones.append(1)
        if self.data_package["month-number-one-2"]:
            ones.append(1)
        if self.data_package["month-number-one-4"]:
            ones.append(1)
        if self.data_package["month-number-one-8"]:
            ones.append(1)
        if self.data_package["month-number-tens-10"]:
            ones.append(1)
        if self.data_package["year-one-1"]:
            ones.append(1)
        if self.data_package["year-one-2"]:
            ones.append(1)
        if self.data_package["year-one-4"]:
            ones.append(1)
        if self.data_package["year-one-8"]:
            ones.append(1)
        if self.data_package["year-tens-10"]:
            ones.append(1)
        if self.data_package["year-tens-20"]:
            ones.append(1)
        if self.data_package["year-tens-40"]:
            ones.append(1)
        if self.data_package["year-tens-80"]:
            ones.append(1)
        if self.data_package["date-parity"]:
            ones.append(1)

        if len(ones) % 2  != 0:
            raise ParityError('date data')

    def _check_data(self):
        if self.data_package['start-bit'] == 1:
            raise ParityError('start-bit')

        if self.data_package['time-begin'] != 1:
            raise ParityError('time-begin-bit')

        self._check_minute()
        self._check_hour()
        self._check_date()

    def _calculate_data(self):
        # time
        minute_one = self.data_package["minute-one-8"] * 8 + self.data_package["minute-one-4"] * 4 + self.data_package["minute-one-2"] * 2 + self.data_package["minute-one-1"] * 1
        minute_tens = self.data_package["minute-tens-40"] * 4 + self.data_package["minute-tens-20"] * 2 + self.data_package["minute-tens-10"] * 1
        minute = str(minute_tens) + str(minute_one)
        hour_one = self.data_package["hour-one-8"] * 8 + self.data_package["hour-one-4"] * 4 + self.data_package["hour-one-2"] * 2 + self.data_package["hour-one-1"] * 1
        hour_tens = self.data_package["hour-tens-20"] * 2 + self.data_package["hour-tens-10"] * 1
        hour = str(hour_tens) + str(hour_one)

        #date 
        day_one = self.data_package["calendar-day-one-1"] * 1 + self.data_package["calendar-day-one-2"] * 2 + self.data_package["calendar-day-one-4"] * 4 + self.data_package["calendar-day-one-8"] * 8
        day_tens = self.data_package["calendar-day-tens-10"] * 1 + self.data_package["calendar-day-tens-20"] * 2
        day = str(day_tens) + str(day_one)

        month_number_one = self.data_package["month-number-one-1"] * 1 + self.data_package["month-number-one-2"] * 2 + self.data_package["month-number-one-4"] * 4 + self.data_package["month-number-one-8"] * 8
        month_number_tens = self.data_package["month-number-tens-10"] * 1
        month_number = str(month_number_tens) + str(month_number_one)

        year_one = self.data_package["year-one-1"] * 1 + self.data_package["year-one-2"] * 2 + self.data_package["year-one-4"] * 4 + self.data_package["year-one-8"] * 8
        year_tens = self.data_package["year-tens-10"] * 1 + self.data_package["year-tens-20"] * 2 + self.data_package["year-tens-40"] * 4 + self.data_package["year-tens-80"] * 8
        year = str(CENTURY) + str(year_tens) + str(year_one)

        weekday = self.data_package["weekday-1"] * 1 + self.data_package["weekday-2"] * 2 + self.data_package["weekday-4"] * 4

        self.datetime['time'] = {'subsecond': 0, 'second': 0, 'minute': int(minute), 'hour': int(hour)}
        self.datetime['date'] = {'day': int(day), 'month_number': int(month_number), 'year': int(year), 'weekday': int(weekday)}

    def _set_rtc(self):
        self.rtc.datetime((
                    self.datetime['date']['year'],
                    self.datetime['date']['month_number'],
                    self.datetime['date']['day'],
                    self.datetime['date']['weekday'],
                    self.datetime['time']['hour'],
                    self.datetime['time']['minute'],
                    self.datetime['time']['second'],
                    self.datetime['time']['subsecond']
                ))

    def sync_internal_clock(self):
        self.log.info("Recieving time signal from DCF77-Transmitter")
        self.log.warning("Be patient it may take up to 5 minutes")
        while self.attempts <= self.max_attempts:
            info_str = "Attempt: " + str(self.attempts) + " / " + str(self.max_attempts)
            self.log.info(info_str)
            try:
                self._find_start_bit()
                self._receive_data()
                self._check_data()
                self._calculate_data()
                self._set_rtc()
                self.success = True
                date_time_str = "Date-Time set to: " + str(self.datetime['date']['day']) + "." + str(self.datetime['date']['month_number']) + "." + str(self.datetime['date']['year']) +" at " + str(self.datetime['time']['hour']) + ":" + str(self.datetime['time']['minute'])
                self.log.info(date_time_str)
                break
            except StartBitError:
                self.attempts = self.attempts + 1
                self.log.error("Cannot find start bit")
            except LogicDurationError:
                self.attempts = self.attempts + 1
                self.log.error("The duration of one logical value is too long.")
            except RecordLengthError:
                self.attempts = self.attempts + 1
                self.log.error("The number of bits in a minute was too much or too little. Some bits may be lost.")
            except ParityError as e:
                self.attempts = self.attempts + 1
                for arg in e.args:
                    error_str = "The value for '" + arg + "' is not correct. The received data is faulty."
                    self.log.error(error_str)
        
        self.attempts = 1
        if not self.success:
            raise TimeSyncError("Unimpossible to set internal RTC")
        self.success = False


   