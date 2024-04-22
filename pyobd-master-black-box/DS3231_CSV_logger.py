import smbus
import datetime
import time
import csv
from obd import OBD, commands


DS3231_I2C_ADDRESS = 0x68
DS3231_REG_SECONDS = 0x00
DS3231_REG_MINUTES = 0x01
DS3231_REG_HOURS = 0x02
DS3231_REG_DAY = 0x03
DS3231_REG_DATE = 0x04
DS3231_REG_MONTH = 0x05
DS3231_REG_YEAR = 0x06

bus = smbus.SMBus(1)

connection = OBD()

def bcd_to_decimal(bcd):
    return (bcd & 0x0F) + ((bcd & 0xF0) >> 4) * 10

def decimal_to_bcd(decimal):
    return ((decimal // 10) << 4) + (decimal % 10)

def read_datetime():
    rtc_bytes = bus.read_i2c_block_data(DS3231_I2C_ADDRESS, DS3231_REG_SECONDS, 7)
    second = bcd_to_decimal(rtc_bytes[0])
    minute = bcd_to_decimal(rtc_bytes[1])
    hour = bcd_to_decimal(rtc_bytes[2] & 0x3F)
    day = bcd_to_decimal(rtc_bytes[3])
    date = bcd_to_decimal(rtc_bytes[4])
    month = bcd_to_decimal(rtc_bytes[5])
    year = bcd_to_decimal(rtc_bytes[6]) + 2000
    return datetime.datetime(year, month, date, hour, minute, second)

def set_datetime(dt):
    rtc_bytes = [
        decimal_to_bcd(dt.second),
        decimal_to_bcd(dt.minute),
        decimal_to_bcd(dt.hour),
        decimal_to_bcd(dt.weekday() + 1), 
        decimal_to_bcd(dt.day),
        decimal_to_bcd(dt.month),
        decimal_to_bcd(dt.year - 2000)
    ]
    bus.write_i2c_block_data(DS3231_I2C_ADDRESS, DS3231_REG_SECONDS, rtc_bytes)

def write_to_csv(filename, data):
    with open(filename, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(data)

if __name__ == "__main__":
    try:
        filename_prefix = datetime.datetime.now().strftime("%Y_%m_%d") + "_"
        file_counter = 1
        while True:
            now = read_datetime()
            date_str = now.strftime("%Y-%m-%d")
            time_str = now.strftime("%H:%M:%S")
            print("date:", date_str)
            print("hour:", time_str)
            data_to_write = [date_str, time_str]
            
            rpm = connection.query(commands.RPM).value.magnitude
            speed = connection.query(commands.SPEED).value.magnitude
            throttle_position = connection.query(commands.THROTTLE_POS).value.magnitude
            load = connection.query(commands.ENGINE_LOAD).value.magnitude
            fuel_status = connection.query(commands.FUEL_STATUS).value.magnitude
            
            data_to_write.extend([rpm, speed, throttle_position, load, fuel_status])
            write_to_csv("datetime_log.csv", data_to_write)
            
            if rpm == 0:
                filename = filename_prefix + str(file_counter) + ".csv"
                write_to_csv(filename, data_to_write)
                file_counter += 1
                print("logging ended, information is in:", filename)
                break
            
            time.sleep(1)
    except KeyboardInterrupt:
        print("exiting")
