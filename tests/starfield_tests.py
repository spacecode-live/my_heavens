"""Tests for the Starfield code."""

    # Copyright (c) 2017 Bonnie Schulkin

    # This file is part of My Heavens.

    # My Heavens is free software: you can redistribute it and/or modify it under
    # the terms of the GNU Affero General Public License as published by the Free
    # Software Foundation, either version 3 of the License, or (at your option)
    # any later version.

    # My Heavens is distributed in the hope that it will be useful, but WITHOUT
    # ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
    # FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License
    # for more details.

    # You should have received a copy of the GNU Affero General Public License
    # along with My Heavens. If not, see <http://www.gnu.org/licenses/>.

import os
from unittest import TestCase
import math
from datetime import datetime
import pytz
import ephem

# be able to import from parent dir
import sys
sys.path.append('..')

from run_tests import MarginTestCase, DbTestCase
from model import Constellation
from starfield import deg_to_rad, rad_to_deg, StarField, BOOTSTRAP_DTIME_FORMAT

MAX_MAG = 5

# acceptable margin when comparing floats
MARGIN = 0.005

# 9pm on March 1, 2017 (local time)
TEST_DATETIME = datetime(2017, 3, 1, 21, 0, 0)
TEST_DATETIME_STRING = datetime.strftime(TEST_DATETIME, BOOTSTRAP_DTIME_FORMAT)

# expected data sets
CONST_LIST_SET = set(['Orion', 'Monoceros', 'Telescopium'])
COORDS_KEY_SET = set(['ra', 'dec'])
SKYOBJECT_KEY_SET = COORDS_KEY_SET | set(['color', 'magnitude', 'name',
    'distance', 'celestialType', 'distanceUnits', 'constellation'])
PLANET_KEY_SET = SKYOBJECT_KEY_SET | set(['size', 'prevRise', 'phase', 'nextSet'])
SUN_KEY_SET = PLANET_KEY_SET
MOON_KEY_SET = PLANET_KEY_SET | set(['colong', 'rotation'])

# expected planets for star field settings 
BRIGHT_PLANET_NAMES_SET = set(['Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn'])

# test lat/lngs: johannesburg
J_LAT = -26.2041
J_LNG = 28.0473
J_LAT_RAD = -0.45734782252184614
J_LNG_RAD = 0.4895177312946056
J_STF = StarField(lat=J_LAT, lng=J_LNG, max_mag=MAX_MAG, 
                  localtime_string=TEST_DATETIME_STRING)

# test lat/lngs: sf
SF_LAT = 37.7749
SF_LNG = -122.4194
SF_LAT_RAD = 0.659296379611606
SF_LNG_RAD = 4.14656370886364
SF_STF = StarField(lat=SF_LAT, lng=SF_LNG, max_mag=MAX_MAG, 
                    localtime_string=TEST_DATETIME_STRING)

# Rigel
R_RA = 1.372
R_DEC = -0.143

# Alpha Tel
AT_RA = 4.851
AT_DEC = -0.801


class StarFieldTestsWithoutDb(MarginTestCase):  
    """Test calculations to retrieve star and constellation data.

    This class is for tests that do not require the database.
    """

    #########################################################
    # degrees -> radians (and reverse) utility functions
    #########################################################

    def test_deg_to_rad_positive(self):
        """Test a positive degrees -> radians conversion."""

        rads = deg_to_rad(90)
        self.assertEqual(rads, math.pi / 2)


    def test_deg_to_rad_negative(self):
        """Test a negative degrees -> radians conversion."""

        rads = deg_to_rad(-180)
        self.assertEqual(rads, -math.pi)


    def test_rad_to_deg_zero(self):
        """Test a zero degrees -> radians conversion."""

        rads = deg_to_rad(0)
        self.assertEqual(rads, 0)


    def test_rad_to_deg_positive(self):
        """Test a positive radians -> degrees conversion."""

        degs = rad_to_deg(math.pi / 2)
        self.assertEqual(degs, 90)


    def test_rad_to_deg_negative(self):
        """Test a negative radians -> degrees conversion."""

        degs = rad_to_deg(-math.pi)
        self.assertEqual(degs, -180)


    def test_deg_to_rad_zero(self):
        """Test a zero radians -> degrees conversion."""

        degs = rad_to_deg(0)
        self.assertEqual(degs, 0)


    #########################################################
    # lat/lng string tests
    #########################################################

    def test_sf_lat(self):
        """Test sf latitude string."""

        lstring = SF_STF.get_lat_or_lng_string('lat')
        self.assertEqual(lstring, '37.77&deg; N')

    def test_sf_lon(self):
        """Test sf longitude string."""

        lstring = SF_STF.get_lat_or_lng_string('lon')
        self.assertEqual(lstring, '122.42&deg; W')

    def test_johannesburg_lat(self):
        """Test johannesburg latitude string."""

        lstring = J_STF.get_lat_or_lng_string('lat')
        self.assertEqual(lstring, '26.20&deg; S')

    def test_johannesburg_lon(self):
        """Test johannesburg longitude string."""

        lstring = J_STF.get_lat_or_lng_string('lon')
        self.assertEqual(lstring, '28.05&deg; E')


    #########################################################
    # starfield spec tests
    #########################################################

    def test_starfield_spec_format(self):
        """Test the format of the dict returned by the starfield spec generator."""

        spec_keys = set(['lat', 'lng', 'dateString', 'timeString'])
        specs = SF_STF.get_specs()

        self.assertEqual(set(specs.keys()), spec_keys)
        self.assertIsInstance(specs['lat'], str)
        self.assertIsInstance(specs['lng'], str)
        self.assertIsInstance(specs['dateString'], str)
        self.assertIsInstance(specs['timeString'], str)

    def test_sf_specs(self):
        """Test specs returned for SF test starfield."""

        specs = SF_STF.get_specs()
        self.assertEqual(specs['lat'], '37.77&deg; N')
        self.assertEqual(specs['lng'], '122.42&deg; W')
        self.assertEqual(specs['dateString'], 'March 1, 2017')
        self.assertEqual(specs['timeString'], '9:00 PM')

    def test_johannesburg_specs(self):
        """Test specs returned for Johannesburg test starfield."""

        specs = J_STF.get_specs()
        self.assertEqual(specs['lat'], '26.20&deg; S')
        self.assertEqual(specs['lng'], '28.05&deg; E')
        self.assertEqual(specs['dateString'], 'March 1, 2017')
        self.assertEqual(specs['timeString'], '9:00 PM')

    #########################################################
    # starfield time zones
    #########################################################

    def timezone_test(self, stf, expected_tz):
        """A generic function to test the timezone determination code."""

        stf.set_timezone()
        self.assertEqual(stf.timezone, expected_tz)

    def test_sf_timezone(self):
        """Test getting time zone for san francisco."""

        self.timezone_test(SF_STF, pytz.timezone('America/Los_Angeles'))

    def test_johannesburg_timezone(self):
        """Test getting time zone for san francisco."""

        self.timezone_test(J_STF, pytz.timezone('Africa/Johannesburg'))

    def test_zero_zero_timezone(self):
        """Test getting time zone for lat/lng that has no time zone.

        In this case, we return utc."""

        stf = StarField(lat=0, lng=0)
        self.timezone_test(stf, pytz.timezone('Etc/UTC'))


    #########################################################
    # starfield with no time provided
    #########################################################

    def test_no_time_provided(self):
        """Test that a starfield gets the time of "now" if no time is provided"""

        stf = StarField(lat=SF_LAT, lng=SF_LNG)
        now = pytz.utc.localize(datetime.utcnow())

        # make sure the time assigned is no more than one second off current time
        self.assertTrue(abs(stf.utctime - now).seconds < 1)


    #########################################################
    # local time to utc
    #########################################################

    def local_to_utc_time_test(self, lat, lng, expected_offset):
        """A generic function to test the starfield set_utc_time method

        expected_offset is a time difference from UTC, in hours"""

        # make a starfield instance with an arbitrary time
        dt_string = datetime.strftime(TEST_DATETIME, BOOTSTRAP_DTIME_FORMAT)
        stf = StarField(lat=lat, lng=lng, localtime_string=dt_string)

        time_diff = stf.utctime - pytz.utc.localize(TEST_DATETIME)
        self.assertEqual(time_diff.seconds, expected_offset * 3600)


    def test_sf_localtime_to_utc(self):
        """Test translating sf localtime to utc."""

        self.local_to_utc_time_test(SF_LAT, SF_LNG, 8)


    def test_johannesburg_localtime_to_utc(self):
        """Test translating johannesburg localtime to utc.

        Note: it won't be a day ahead because of the way I'm testing 
        (hence the 22 instead of -2 for the offset)"""

        self.local_to_utc_time_test(J_LAT, J_LNG, 22)


    #########################################################
    # making pyEphem ephemeris
    #########################################################

    def make_ephem_test(self, stf):
        """Generic test for making a pyEphem ephemeris."""

        stf.make_ephem()
        self.assertIsInstance(stf.ephem, ephem.Observer)


    def test_sf_ephem(self):
        """Test making ephemeris for SF."""

        self.make_ephem_test(SF_STF)


    def test_johannesburg_ephem(self):
        """Test making ephemeris for Johannesburg."""

        self.make_ephem_test(J_STF)

    #########################################################
    # get local time from ephem time
    #########################################################

    #########################################################
    # generic solar system data tests
    #########################################################

    def ss_data_format_test(self, key_set, pdata, celestial_type):
        """Generic test for ephemeris data format."""

        self.assertIsInstance(pdata, dict)
        self.assertEqual(set(pdata.keys()), key_set)
        self.assertIsInstance(pdata['ra'], float)
        self.assertIsInstance(pdata['dec'], float)
        self.assertIsInstance(pdata['magnitude'], float)
        self.assertIsInstance(pdata['name'], str)
        self.assertEqual(pdata['color'][0], '#') # color should be a hex color string
        self.assertIsInstance(pdata['size'], float)
        self.assertIsInstance(pdata['distance'], str)
        self.assertIsInstance(pdata['celestialType'], str)
        self.assertIsInstance(pdata['nextSet'], str)
        self.assertEqual(pdata['distanceUnits'], 'AU')
        self.assertIsInstance(pdata['prevRise'], str)
        self.assertIsInstance(pdata['phase'], str)
        self.assertIsInstance(pdata['constellation'], str)
        self.assertEqual(pdata['celestialType'], celestial_type)


    #########################################################
    # get rise and set times
    #########################################################

    def get_rise_set_times_test(self, stf, obj, expected_rise, expected_set):
        """Generic test to get the rise / set times."""

        trise, tset = stf.get_rise_set_times(obj(stf.ephem))
        self.assertEqual(trise, expected_rise)
        self.assertEqual(tset, expected_set)

    def test_sf_moon_riseset(self):
        """Test rise and set times for moon for sf starfield."""

        trise = '8:40 AM'
        tset = '9:43 PM'

        self.get_rise_set_times_test(SF_STF, ephem.Moon, trise, tset)

    def test_johannesburg_moon_riseset(self):
        """Test rise and set times for moon for johannesburg starfield."""

        trise = '8:37 AM'
        tset = '9:30 PM'

        self.get_rise_set_times_test(J_STF, ephem.Moon, trise, tset)

    #########################################################
    # individual planet data tests
    #########################################################

    def test_planet_data_format(self):
        """Test the format of data returned from get_planet_data."""
        
        # actual stf and planet are inconsequential here
        pdata = SF_STF.get_planet_data(ephem.Mars)
        self.ss_data_format_test(PLANET_KEY_SET, pdata, 'planet')

    def get_planet_data_test(self, stf, planet, expected_ra, expected_dec):
        """Generic test for getting planet data."""

        pdata = stf.get_planet_data(planet)

        # how much 'slop' we'll allow before deciding it's the wrong answer
        margin = 0.0001

        self.assertWithinMargin(pdata['ra'], expected_ra, margin)
        self.assertWithinMargin(pdata['dec'], expected_dec, margin)

    def test_sf_mars_data(self):
        """Test position of mars for SF, visible at test datetime."""

        # expected data
        ra = 337.4816817093629
        dec = 9.466995889404037

        self.get_planet_data_test(SF_STF, ephem.Mars, ra, dec)

    def test_sf_saturn_data(self):
        """Test position of saturn for SF, not visible at test datetime."""

        # expected data
        ra = 93.45764161796552
        dec = -22.089550180792546

        self.get_planet_data_test(SF_STF, ephem.Saturn, ra, dec)

    def test_johannesburg_mars_data(self):
        """Test position of mars for johannesburg, not visible at test datetime."""

        # expected data
        ra = 337.7657593061578
        dec = 9.351677268540211

        self.get_planet_data_test(J_STF, ephem.Mars, ra, dec)

    def test_johannesburg_jupiter_data(self):
        """Test position of jupiter for johannesburg, visible at test datetime."""

        # expected data
        ra = 158.82593840533076
        dec = -7.263921571076729

        self.get_planet_data_test(J_STF, ephem.Jupiter, ra, dec)


    #########################################################
    # collective planet data tests
    #########################################################

    def get_planets_test(self, stf):
        """Generic test to get planets."""

        planets = stf.get_planets()

        # get a set of the planet names
        planet_names = set(p['name'] for p in planets)

        # all suitably bright planets should be returned
        self.assertEqual(planet_names, BRIGHT_PLANET_NAMES_SET)

    def test_johannesburg_planets(self):
        """Test Johannesburg planet set for the test date and time."""

        self.get_planets_test(J_STF)

    def test_sf_planets(self):
        """Test San Francisco planet set for the test date and time."""

        self.get_planets_test(SF_STF)

    #########################################################
    # sun data tests
    #########################################################

    def test_sun_data_format(self):
        """Test format of sun data."""

        sdata = SF_STF.get_sun()
        self.ss_data_format_test(SUN_KEY_SET, sdata, 'star')

    #########################################################
    # moon data tests
    #########################################################

    def test_moon_data_format(self):
        """Test format of returned moon data."""

        mdata = SF_STF.get_moon()
        self.ss_data_format_test(MOON_KEY_SET, mdata, 'moon')

    def test_moon_specific_data_format(self):
        """Test format of data specific to the moon."""

        mdata = SF_STF.get_moon()
        self.assertIsInstance(mdata['colong'], float)
        self.assertIsInstance(mdata['rotation'], float)


    def moon_data_test(self, stf, ra, dec, phase, colong, rotation, trise, tset):
        """Generic test for moon data."""

        mdata = SF_STF.get_moon()
        self.assertEqual(mdata['ra'], ra)
        self.assertEqual(mdata['dec'], dec)
        self.assertEqual(mdata['phase'], phase)
        self.assertEqual(mdata['colong'], colong)
        self.assertEqual(mdata['rotation'], rotation)
        self.assertEqual(mdata['prevRise'], trise)
        self.assertEqual(mdata['nextSet'], tset)


    def test_sf_moon_data(self):
        """Test moon data for San Francisco."""

        # expected data
        ra = 332.8583815004972
        dec = 6.260453993509564
        phase = 'waxing crescent: 16.1'
        colong = 318.9918500407805
        rotation = 383.33266920101795
        trise = '8:40 AM'
        tset = '9:43 PM'

        self.moon_data_test(SF_STF, ra, dec, phase, colong, rotation, trise, tset)


    def test_johannesburg_moon_data(self):
        """Test moon data for Johannesburg"""

        # expected data
        ra = 332.8583815004972
        dec = 6.260453993509564
        phase = 'waxing crescent: 16.1'
        colong = 318.9918500407805
        rotation = 383.33266920101795
        trise = '8:40 AM'
        tset = '9:43 PM'

        self.moon_data_test(J_STF, ra, dec, phase, colong, rotation, trise, tset)


    #########################################################
    # moon phase phrase tests
    #########################################################


    #########################################################
    # moon rotation tests
    #########################################################


    #########################################################
    # sky rotation tests
    #########################################################
