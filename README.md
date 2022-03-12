NinjaLooter Raid Manager for EQ
===============================

Designed to handle looting for Plane of Sky with the Federation,
but should work in many other cases.

Copy `ninjalooter.ini.example` to `ninjalooter.ini` and configure
your log path, run `pip install -e .`, and you should be good to go!

It will handle:

Bidding
-------
![Bidding Tab](ninjalooter_bid_tab.png)

Attendance Management
---------------------
![Attendance Management Tab](ninjalooter_attendance_tab.png)

Population Rolls
----------------
![Population Roll Tab](ninjalooter_pop_tab.png)

Time of Death Tracking
----------------------
![Time of Death Tracking](ninjalooter_tod_tracking_tab.png)

Testing
=======

Install `tox`

Run: `tox -e [pep8,pylint,coverage]`

Building
========

Install `pyinstaller`

Run: `pyinstaller --onefile ninjalooter_py.spec`