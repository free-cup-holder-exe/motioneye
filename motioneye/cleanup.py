# Copyright (c) 2013 Calin Crisan
# This file is part of motionEye.
#
# motionEye is free software: you can redistribute it and/or modify
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

import datetime
import logging
import threading

from tornado.ioloop import IOLoop

from motioneye import mediafiles, settings

_thread = None


def start():
    if not settings.CLEANUP_INTERVAL:
        return

    # schedule the first call a bit later to improve performance at startup
    io_loop = IOLoop.current()
    io_loop.add_timeout(
        datetime.timedelta(seconds=min(settings.CLEANUP_INTERVAL, 60)), _run_process
    )


def stop():
    global _thread

    if not running():
        _thread = None
        return

    _thread.join(timeout=10)

    if _thread.is_alive():
        # a daemon thread, it dies with the process
        logging.error('cleanup did not finish in time, abandoning it...')

    _thread = None


def running():
    return _thread is not None and _thread.is_alive()


def _run_process():
    global _thread

    io_loop = IOLoop.current()

    # schedule the next call
    io_loop.add_timeout(
        datetime.timedelta(seconds=settings.CLEANUP_INTERVAL), _run_process
    )

    if not running():  # check that the previous run has finished
        logging.debug('running cleanup process...')

        _thread = threading.Thread(target=_do_cleanup, name='cleanup', daemon=True)
        _thread.start()


def _do_cleanup():
    # this will be executed in a separate thread

    try:
        mediafiles.cleanup_media('picture')
        mediafiles.cleanup_media('movie')
        logging.debug('cleanup done')

    except Exception as e:
        logging.error(f'failed to cleanup media files: {str(e)}', exc_info=True)
