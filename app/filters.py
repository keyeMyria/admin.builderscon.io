# coding:utf-8

import admin
import iso8601
import pytz

months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
class Date(object):
    def __init__(self, jsonval, lang='en', timezone='UTC'):
        localtz = pytz.timezone(timezone)
        self.open = iso8601.parse_date(jsonval.get('open')).astimezone(localtz)
        self.close = iso8601.parse_date(jsonval.get('close')).astimezone(localtz)
        self.lang = lang

    def date(self):
        return '%d年%d月%d日'.decode('utf-8') % (self.open.year, self.open.month, self.open.day)

    def open_time(self):
        return '%02d:%02d' % (self.open.hour, self.open.minute)

    def close_time(self):
        return '%02d:%02d' % (self.close.hour, self.close.minute)

    def __str__(self):
        return self.date()



@admin.app.template_filter('date')
def date_filter(s, lang='en', timezone='UTC'):
    return Date(s, lang=lang, timezone=timezone)
