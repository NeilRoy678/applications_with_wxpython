import controller

import os
import pathlib
import time
import wx

from ObjectListView import ObjectListView, ColumnDefn

wildcard = "Tar (*.tar)|*.tar|" \
           "Zip (*.zip)|*.zip"

open_wildcard = "All files (*.*)|*.*"

class Items:

    def __init__(self, path, name, size, item_type,
                 modified):
        self.path = path
        self.name = name
        self.size = size
        self.item_type = item_type
        self.modified = modified


class DropTarget(wx.FileDropTarget):

    def __init__(self, window):
        super().__init__()
        self.window = window

    def OnDropFiles(self, x, y, filenames):
        self.window.update_display(filenames)
        return True

class ArchivePanel(wx.Panel):


    def __init__(self, parent):
        super().__init__(parent)
        drop_target = DropTarget(self)
        self.archive_items = []
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        paths = wx.StandardPaths.Get()
        self.current_directory = paths.GetDocumentsDir()

        self.archive_olv = ObjectListView(
            self, style=wx.LC_REPORT|wx.SUNKEN_BORDER)
        self.archive_olv.SetEmptyListMsg("Add Files / Folders here")
        self.archive_olv.SetDropTarget(drop_target)
        self.update_archive()
        main_sizer.Add(self.archive_olv, 1, wx.ALL|wx.EXPAND, 5)


        h_sizer = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, label='File name:')
        h_sizer.Add(label)
        self.archive_filename = wx.TextCtrl(self)
        h_sizer.Add(self.archive_filename, 1, wx.EXPAND)
        self.archive_types = wx.ComboBox(
            self, value='Tar',
            choices=['Tar'],
            size=(75, -1))
        h_sizer.Add(self.archive_types, 0)
        main_sizer.Add(h_sizer, 0, wx.EXPAND)

        create_archive_btn = wx.Button(self, label='Create Archive')
        create_archive_btn.Bind(wx.EVT_BUTTON, self.on_create_archive)
        main_sizer.Add(create_archive_btn, 0, wx.ALL|wx.CENTER, 5)

        self.SetSizer(main_sizer)

    def on_create_archive(self, event):
        if not self.archive_olv.GetObjects():
            self.show_message('No files / folders to archive',
                              'Error', wx.ICON_ERROR)
            return

        dlg = wx.DirDialog(self, "Choose a directory:",
                           style=wx.DD_DEFAULT_STYLE,
                           defaultPath=self.current_directory)
        archive_filename = self.archive_filename.GetValue()
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.current_directory = path
            archive_type = self.archive_types.GetValue()

            full_save_path = pathlib.Path(
                path, '{filename}.{type}'.format(
                    filename=archive_filename,
                    type=archive_type.lower()
                ))
            controller.create_archive(
                full_save_path,
                self.archive_olv.GetObjects(),
                archive_type)
            message = f'Archive created at {full_save_path}'
            self.show_message(message, 'Archive Created',
                              wx.ICON_INFORMATION)
        dlg.Destroy()

    def update_archive(self):
        self.archive_olv.SetColumns([
                            ColumnDefn("Name", "left", 350, "name"),
                            ColumnDefn("Size", "left", 75, "size"),
                            ColumnDefn("Type", "right", 75, "item_type"),
                            ColumnDefn("Modified", "left", 150, "modified")
                        ])
        self.archive_olv.SetObjects(self.archive_items)

    def update_display(self, items):
        paths = [pathlib.Path(item) for item in items]
        for path in paths:
            basename = path.name
            size = self.get_size(path)
            if path.is_dir():
                item_type = 'folder'
            else:
                item_type = 'file'
            last_modified = time.ctime(path.stat().st_mtime)
            item = Items(path, basename, size, item_type,
                         last_modified)
            self.archive_items.append(item)

        self.update_archive()

    def get_size(self, path):
        size = path.stat().st_size

        suffixes = ['B', 'KB', 'MB', 'GB', 'TB']
        index = 0
        while size > 1024:
            index += 1
            size = size / 1024.0

        suffix = suffixes[index]
        return f'{size:.1f} {suffix}'

    def show_message(self, message, caption, flag=wx.ICON_ERROR):
        """
        Show a message dialog
        """
        msg = wx.MessageDialog(None, message=message,
                               caption=caption, style=flag)
        msg.ShowModal()
        msg.Destroy()



class MainFrame(wx.Frame):

    def __init__(self):
        """Constructor"""
        super().__init__(
            None, title="PyArchiver",
            size=(800, 600))
        self.panel = ArchivePanel(self)
        self.create_menu()

        self.Show()

    def create_menu(self):
        menu_bar = wx.MenuBar()

        # Create file menu
        file_menu = wx.Menu()

        exit_menu_item = file_menu.Append(
            wx.NewId(), "Exit",
            "Exit the application")
        menu_bar.Append(file_menu, '&File')
        self.Bind(wx.EVT_MENU, self.on_exit, exit_menu_item)

        # Create edit menu
        edit_menu = wx.Menu()

        add_file_menu_item = edit_menu.Append(
            wx.NewId(), 'Add File',
            'Add a file to be archived')
        self.Bind(wx.EVT_MENU, self.on_add_file, add_file_menu_item)

        remove_menu_item = edit_menu.Append(
            wx.NewId(), 'Remove File/Folder',
            'Remove a file or folder')
        menu_bar.Append(edit_menu, 'Edit')

        self.SetMenuBar(menu_bar)

    def on_add_file(self, event):
        dlg = wx.FileDialog(
        self, message="Choose a file",
            defaultDir=self.panel.current_directory,
            defaultFile="",
            wildcard=open_wildcard,
            style=wx.FD_OPEN | wx.FD_MULTIPLE | wx.FD_CHANGE_DIR
        )
        if dlg.ShowModal() == wx.ID_OK:
            paths = dlg.GetPaths()
        dlg.Destroy()

    def on_exit(self, event):
        self.Close()

    def on_remove(self, event):
        pass

if __name__ == "__main__":
    app = wx.App(False)
    frame = MainFrame()
    app.MainLoop()