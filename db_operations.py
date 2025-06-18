# Import required dependencies
import aiosqlite

db_name = 'UserData.db'

async def insert_reminder_data(reminder_data):
    async with aiosqlite.connect(db_name) as db:
        cursor = await db.cursor()
        await cursor.execute("INSERT INTO ReminderData (UserID, Fajr, Sunrise, Dhuhr, Asr, HanafiAsr, Maghrib, Isha, Midnight, Country, City, TimeZone, Date, School, MidnightMode, Method, HourFormat, RemindEarly, BeforeDhuhr) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", reminder_data)
        await db.commit()

async def delete_reminder_data(user_id):
    async with aiosqlite.connect(db_name) as db:
        cursor = await db.cursor()
        await cursor.execute("DELETE FROM ReminderData WHERE UserID = (?)", (user_id,))
        await db.commit()

async def update_reminder_data(user_id, info_to_update, new_info):
    async with aiosqlite.connect(db_name) as db:
        cursor = await db.cursor()
        if info_to_update != "Selected Prayers":
            await cursor.execute(f"UPDATE ReminderData SET {info_to_update} = (?) WHERE UserID = (?)", (new_info, user_id))
        else:
            await cursor.execute("UPDATE ReminderData SET Fajr = (?), Sunrise = (?), Dhuhr = (?), Asr = (?), HanafiAsr = (?), Maghrib = (?), Isha = (?), Midnight = (?) WHERE UserID = (?)", new_info + [user_id])
        await db.commit()
        
async def get_db_prayers(user_id):
    async with aiosqlite.connect(db_name) as db:
        cursor = await db.cursor()
        await cursor.execute("SELECT Fajr, Sunrise, Dhuhr, Asr, HanafiAsr, Maghrib, Isha, Midnight FROM ReminderData WHERE UserID = (?)", (user_id,))
        selected_prayers_timings = await cursor.fetchone()
        selected_prayers = []
        column_names = ['Fajr', 'Sunrise', 'Dhuhr', 'Asr', 'HanafiAsr', 'Maghrib', 'Isha', 'Midnight']
        # Putting None in place of timings that are not selected, and the name of the timing if it is selected
        for column_num in range(8):
            if selected_prayers_timings[column_num] is not None:
                selected_prayers.append(column_names[column_num])
            else:
                selected_prayers.append(None)
        return selected_prayers

async def get_prayer_timings_data(user_id):
    async with aiosqlite.connect(db_name) as db:
        cursor = await db.cursor()
        await cursor.execute("SELECT Country, City, Date, School, MidnightMode, Method FROM ReminderData WHERE UserID = (?)", (user_id,))
        info = await cursor.fetchone()
        return info

async def user_reminder_data_exists(user_id):
    async with aiosqlite.connect(db_name) as db:
        cursor = await db.cursor()
        await cursor.execute("SELECT UserID FROM ReminderData WHERE UserID = (?)", (user_id,))
        data = await cursor.fetchone()
        return data is not None

async def get_reminder_user_ids():
    async with aiosqlite.connect(db_name) as db:
        cursor = await db.cursor()
        await cursor.execute("SELECT UserID FROM ReminderData")
        user_ids = await cursor.fetchall()
        return user_ids

async def get_reminder_info(user_id, field):
    async with aiosqlite.connect(db_name) as db:
        cursor = await db.cursor()
        await cursor.execute(f"SELECT {field} FROM ReminderData WHERE UserID = (?)", (user_id,))
        data = await cursor.fetchone()
        return data[0]

async def get_stored_prayer_timings(user_id):
    async with aiosqlite.connect(db_name) as db:
        cursor = await db.cursor()
        await cursor.execute("SELECT Fajr, Dhuhr, Asr, Maghrib, Isha FROM ReminderData WHERE UserID = (?)", (user_id,))
        prayer_timings = await cursor.fetchone()
        return prayer_timings

async def get_tracker_info(user_id, field):
    async with aiosqlite.connect(db_name) as db:
        cursor = await db.cursor()
        await cursor.execute(f"SELECT {field} FROM TrackerData WHERE TrackerUserID = (?)", (user_id,))
        data = await cursor.fetchone()
        return data

async def get_tracker_prayer_markers(user_id):
    async with aiosqlite.connect(db_name) as db:
        cursor = await db.cursor()
        await cursor.execute("SELECT Fajr, Dhuhr, Asr, Maghrib, Isha FROM TrackerData WHERE TrackerUserID = (?)", (user_id,))
        prayer_markers = await cursor.fetchone()
        return prayer_markers

async def reset_tracker_markers(user_id):
    async with aiosqlite.connect(db_name) as db:
        cursor = await db.cursor()
        await cursor.execute("UPDATE TrackerData SET Fajr = NULL, Dhuhr = NULL, Asr = NULL, Maghrib = NULL, Isha = NULL WHERE TrackerUserID = (?)", (user_id,))
        await db.commit()

async def update_tracker_data(user_id, field, value):
    async with aiosqlite.connect(db_name) as db:
        cursor = await db.cursor()
        await cursor.execute(f"UPDATE TrackerData SET {field} = (?) WHERE TrackerUserID = (?)", (value, user_id))
        await db.commit()

async def insert_tracker_user_id(user_id):
    async with aiosqlite.connect(db_name) as db:
        cursor = await db.cursor()
        await cursor.execute("INSERT INTO TrackerData (TrackerUserID) VALUES (?)", (user_id,))
        await db.commit()

async def insert_daily_data(table_name, user_id, timezone, time_to_send, date, language):
    if table_name == 'DailyHadithData':
        user_id_field = 'HadithUserID'
    else:
        user_id_field = 'VerseUserID'
    async with aiosqlite.connect(db_name) as db:
        cursor = await db.cursor()
        await cursor.execute(f"INSERT INTO {table_name} ({user_id_field}, Timezone, TimeToSend, MessageSent, Date, Language) VALUES (?, ?, ?, ?, ?, ?)", (user_id, timezone, time_to_send, 0, date, language))
        await db.commit()

async def get_daily_data(table_name, user_id, field):
    if table_name == 'DailyHadithData':
        user_id_field = 'HadithUserID'
    else:
        user_id_field = 'VerseUserID'
    async with aiosqlite.connect(db_name) as db:
        cursor = await db.cursor()
        await cursor.execute(f"SELECT {field} FROM {table_name} WHERE {user_id_field} = (?)", (user_id,))
        data = await cursor.fetchone()
        return data

async def update_daily_data(table_name, user_id, field, value):
    if table_name == 'DailyHadithData':
        user_id_field = 'HadithUserID'
    else:
        user_id_field = 'VerseUserID'
    async with aiosqlite.connect(db_name) as db:
        cursor = await db.cursor()
        await cursor.execute(f"UPDATE {table_name} SET {field} = (?) WHERE {user_id_field} = (?)", (value, user_id))
        await db.commit()

async def delete_daily_data(table_name, user_id):
    if table_name == 'DailyHadithData':
        user_id_field = 'HadithUserID'
    else:
        user_id_field = 'VerseUserID'
    async with aiosqlite.connect(db_name) as db:
        cursor = await db.cursor()
        await cursor.execute(f"DELETE FROM {table_name} WHERE {user_id_field} = (?)", (user_id,))
        await db.commit()

async def get_daily_user_ids(table_name):
    if table_name == 'DailyHadithData':
        user_id_field = 'HadithUserID'
    else:
        user_id_field = 'VerseUserID'
    async with aiosqlite.connect(db_name) as db:
        cursor = await db.cursor()
        await cursor.execute(f"SELECT {user_id_field} FROM {table_name}")
        user_ids = await cursor.fetchall()
        return user_ids