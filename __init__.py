import os
from time import time
from cudatext import *
from .git_manager import GitManager

GIT_TIMEOUT = 5

CELL_TAG_INFO = 20 #CudaText built-in value for last statusbar cell
CELL_TAG = 100 #uniq value for all plugins adding cells via statusbar_proc()

fn_config = os.path.join(app_path(APP_DIR_SETTINGS), 'cuda_git_status.ini')

gitmanager = GitManager()


class Command:
    def __init__(self):

        self.is_loading_sesh = False # to ignore 'on_open()' while loading session
        self.badge_getters = []

        self.load_ops()

        #insert our cell before "info" cell
        index = statusbar_proc('main', STATUSBAR_FIND_CELL, value=CELL_TAG_INFO)
        if not index:
            index = -1
        statusbar_proc('main', STATUSBAR_ADD_CELL, index=index, tag=CELL_TAG)
        statusbar_proc('main', STATUSBAR_SET_CELL_ALIGN, tag=CELL_TAG, value='C')

        imglist = statusbar_proc('main', STATUSBAR_GET_IMAGELIST)
        if not imglist:
            imglist = imagelist_proc(0, IMAGELIST_CREATE)
            statusbar_proc('main', STATUSBAR_SET_IMAGELIST, value=imglist)

        fn_icon = os.path.join(
                    os.path.dirname(__file__),
                    'git-branch.png' if not self.white_icon else 'git-branch_white.png'
                    )

        self.icon_index = imagelist_proc(imglist, IMAGELIST_ADD, value=fn_icon)


    def load_ops(self):

        self.cell_width = int(ini_read(fn_config, 'op', 'statusbar_cell_width', '150'))
        self.white_icon = ini_read(fn_config, 'op', 'white_icon', '0') == '1'
        gitmanager.git = ini_read(fn_config, 'op', 'git_program', 'git')

    def save_ops(self):

        ini_write(fn_config, 'op', 'statusbar_cell_width', str(self.cell_width))
        ini_write(fn_config, 'op', 'white_icon', '1' if self.white_icon else '0')
        ini_write(fn_config, 'op', 'git_program', gitmanager.git)

    def open_config(self):

        self.save_ops()
        if os.path.isfile(fn_config):
            file_open(fn_config)

    def request_update(self, ed_self):

        if self.is_loading_sesh:
            return

        filename = (ed_self or ed).get_filename()

        badge_getter = gitmanager.badge(filename)
        self.badge_getters.append((time(), badge_getter))

        timer_proc(TIMER_START, self.on_timer, 50)

    def on_timer(self, tag='', info=''):

        if self.badge_getters:
            start_time, badge_getter = self.badge_getters[0]
            if time() - start_time > GIT_TIMEOUT:
                del self.badge_getters[0]
            else:
                badge = next(badge_getter)
                if badge is not None:
                    self.update(badge)
                    del self.badge_getters[0]
                else:
                    return

        if not self.badge_getters:
            timer_proc(TIMER_STOP, self.on_timer, 0)

    def update(self, badge):

        statusbar_proc('main', STATUSBAR_SET_CELL_TEXT, tag=CELL_TAG, value=badge)

        #show icon?
        icon = self.icon_index if badge else -1
        statusbar_proc('main', STATUSBAR_SET_CELL_IMAGEINDEX, tag=CELL_TAG, value=icon)

        #show panel?
        size = self.cell_width if badge else 0
        statusbar_proc('main', STATUSBAR_SET_CELL_SIZE, tag=CELL_TAG, value=size)


    def on_tab_change(self, ed_self):
        self.request_update(ed_self)

    def on_open(self, ed_self):
        self.request_update(ed_self)

    def on_save(self, ed_self):
        self.request_update(ed_self)

    def on_state(self, ed_self, state):
        if state == APPSTATE_SESSION_LOAD_BEGIN: # started
            self.is_loading_sesh = True

        elif state in [APPSTATE_SESSION_LOAD_FAIL, APPSTATE_SESSION_LOAD]: # ended
            self.is_loading_sesh = False
            self.request_update(ed)