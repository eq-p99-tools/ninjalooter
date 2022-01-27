# pylint: disable=no-member,invalid-name,protected-access

import string
import time

import wx


def _HandleTypingEvent(self, evt):
    """
    """
    if self.GetItemCount() == 0 or self.GetColumnCount() == 0:
        return False

    if evt.GetModifiers() != 0 and evt.GetModifiers() != wx.MOD_SHIFT:
        return False

    if evt.GetKeyCode() > wx.WXK_START:
        return False

    if evt.GetKeyCode() in (wx.WXK_BACK, wx.WXK_DELETE):
        self.searchPrefix = ""
        return True

    # On which column are we going to compare values?
    # If we should search on the
    # sorted column, and there is a sorted column and it is searchable,
    # we use that
    # one, otherwise we fallback to the primary column
    if self.typingSearchesSortColumn and self.GetSortColumn(
    ) and self.GetSortColumn().isSearchable:
        searchColumn = self.GetSortColumn()
    else:
        searchColumn = self.GetPrimaryColumn()

    # On Linux, GetUnicodeKey() always returns 0 -- on my 2.8.7.1
    # (gtk2-unicode)
    if evt.GetUnicodeKey() == 0:
        uniChar = chr(evt.GetKeyCode())
    else:
        uniChar = chr(evt.GetUnicodeKey())
    if uniChar not in string.printable:
        return False

    # On Linux, evt.GetTimestamp() isn't reliable so use time.time()
    # instead
    timeNow = time.time()
    if (timeNow - self.whenLastTypingEvent) > self.SEARCH_KEYSTROKE_DELAY:
        self.searchPrefix = uniChar
    else:
        self.searchPrefix += uniChar
    self.whenLastTypingEvent = timeNow

    # self.__rows = 0
    self._FindByTyping(searchColumn, self.searchPrefix)
    # print "Considered %d rows in %2f secs" % (self.__rows, time.time() -
    # timeNow)

    return True
