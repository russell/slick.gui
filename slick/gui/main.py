#############################################################################
#
# Copyright (c) 2009 Victorian Partnership for Advanced Computing Ltd and
# Contributors.
# All Rights Reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

import logging

import pygtk
pygtk.require('2.0')
import gobject
import gtk
from arcs.gsi import Certificate
import slick.settings

import os, datetime
from os import path

# idp information
from slick.client import spUri
from slick.shibboleth import list_idps
from urllib2 import urlparse

homedir = os.getenv('USERPROFILE') or os.getenv('HOME')
store_dir = path.join(homedir, ".globus-slcs")


def certificate_expirytime(tray):
    cert = Certificate(path.join(store_dir, 'usercert.pem'))
    time = cert.get_times()[1]
    d1 = datetime.datetime.strptime(str(time), "%b %d %H:%M:%S %Y %Z")
    d2 = datetime.datetime.now()
    tray.statusIcon.set_tooltip(str(d1 - d2))
    gobject.timeout_add(300000, certificate_expirytime, tray)

class SlickPreferences:
    def __init__(self, settings):
        self.settings = settings
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)

        self.window.set_title("Preferences")
        self.window.set_border_width(10)

        self.mainbox = gtk.VBox(False, 0)
        self.window.add(self.mainbox)

        self.idp_box = gtk.HBox(False, 0)
        self.mainbox.pack_start(self.idp_box, False, False, 0)

        idps_label = gtk.Label("IDP")
        self.idp_box.pack_start(idps_label, False, False, 10)
        self.idps = gtk.combo_box_new_text()
        self.idp_box.pack_start(self.idps, True, True, 0)


        # seperator
        separator = gtk.HSeparator()
        self.mainbox.pack_start(separator, False, True, 5)

        # button box for save and quit buttons
        self.button_box = gtk.HButtonBox()
        self.button_box.set_layout(gtk.BUTTONBOX_END)
        self.button_box.set_spacing(10)
        self.mainbox.pack_start(self.button_box, False, False, 0)

        # save and quit buttons
        close_button = gtk.Button(stock=gtk.STOCK_CLOSE)
        close_button.connect("clicked", self.close_cb)
        self.button_box.pack_end(close_button, False, False, 10)

        self.window.set_position(gtk.WIN_POS_CENTER)

        self.show()


    def show(self):
        slcs_login_url = urlparse.urljoin(self.settings.slcs, 'login')
        idp_keys = list_idps(slcs_login_url).keys()
        idp_keys.sort()
        for i in idp_keys:
            self.idps.append_text(i)
            if i == self.settings.idp:
                self.idps.set_active(len(self.idps.get_model())-1)
        self.window.show_all()

    def close_cb(self, widget, data=None):
        self.settings.idp = self.idps.get_active_text()
        self.settings.save()
        self.idps.get_model().clear()
        self.window.hide_all()



class SlickTray:

    def __init__(self, settings):
        self.settings = settings
        self.statusIcon = gtk.StatusIcon()
        self.statusIcon.set_from_stock(gtk.STOCK_YES)
        self.statusIcon.set_visible(True)
        certificate_expirytime(self)

        self.menu = gtk.Menu()
        menuItem = gtk.ImageMenuItem(gtk.STOCK_REFRESH)
        menuItem.connect('activate', self.refresh_certificate_cb, self.statusIcon)
        menuItem.set_property('label', 'Refresh Certificate')
        self.menu.append(menuItem)
        menuItem = gtk.ImageMenuItem(gtk.STOCK_PREFERENCES)
        menuItem.connect('activate', self.preferences_cb, self.statusIcon)
        self.menu.append(menuItem)
        menuItem = gtk.ImageMenuItem(gtk.STOCK_ABOUT)
        menuItem.connect('activate', self.about_cb, self.statusIcon)
        self.menu.append(menuItem)
        menuItem = gtk.ImageMenuItem(gtk.STOCK_QUIT)
        menuItem.connect('activate', self.quit_cb, self.statusIcon)
        self.menu.append(menuItem)

        self.statusIcon.connect('popup-menu', self.popup_menu_cb, self.menu)
        self.statusIcon.set_visible(1)
        #window = SlickPreferences(settings)
        self.preferences = None


    def refresh_certificate_cb(self, widget, event, data = None):
        pass

    def preferences_cb(self, widget, event, data = None):
        if self.preferences:
            self.preferences.show()
        else:
            self.preferences = SlickPreferences(self.settings)

    def quit_cb(self, widget, data = None):
        gtk.main_quit()

    def about_cb(self, widget, data = None):
        about = gtk.AboutDialog()
        about.set_program_name("Slick")
        about.set_version("0.1")
        about.set_copyright("(c) Russell Sim")
        about.set_comments("A Simple tool for keeping you slc")
        #about.set_website("")
        #about.set_logo(gtk.gdk.pixbuf_new_from_file("battery.png"))
        about.run()
        about.destroy()


    def popup_menu_cb(self, widget, button, time, data = None):
        if button == 3:
            if data:
                data.show_all()
                data.popup(None, None, gtk.status_icon_position_menu,
                         3, time, self.statusIcon)


def main():
    # Late import, in case this project becomes a library, never to be run as main again.
    import optparse

    # Populate our options, -h/--help is already there for you.
    optp = optparse.OptionParser()
    optp.add_option('-v', '--verbose', dest='verbose', action='count',
                    help="Increase verbosity (specify multiple times for more)")
    # Parse the arguments (defaults to parsing sys.argv).
    opts, args = optp.parse_args()

    # Here would be a good place to check what came in on the command line and
    # call optp.error("Useful message") to exit if all it not well.

    log_level = logging.WARNING # default
    if opts.verbose == 1:
        log_level = logging.INFO
    elif opts.verbose >= 2:
        log_level = logging.DEBUG

    # Set up basic configuration, out to stderr with a reasonable default format.
    logging.basicConfig(level=log_level)

    # Do some actual work.
    settings = slick.settings.Settings()
    slickTray = SlickTray(settings)
    gtk.main()

if '__main__' == __name__:
    main()
