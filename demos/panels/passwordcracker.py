import wx

from hashlib import md5, sha1, sha224, sha256, sha384, sha512
import random


class PasswordCrackerPanel(wx.Panel):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent=parent)

		self.label_1 = wx.StaticText(self, -1, "Choose a password: ")
		self.passwd_entry = wx.TextCtrl(self, -1, "")
		self.save_passwd_btn = wx.Button(self, -1, "Save password")
		self.label_2 = wx.StaticText(self, -1, "Hashed password:")
		self.hash_entry = wx.TextCtrl(self, -1, "")
		self.crack_passwd_btn = wx.Button(self, -1, "Crack password")

		grid_sizer_1 = wx.FlexGridSizer(3, 3, 0, 1)
		grid_sizer_1.Add(self.label_1, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
		grid_sizer_1.Add(self.passwd_entry, 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0)
		grid_sizer_1.Add(self.save_passwd_btn, 0, wx.ALIGN_CENTER_VERTICAL, 0)
		grid_sizer_1.Add(self.label_2, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
		grid_sizer_1.Add(self.hash_entry, 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0)
		grid_sizer_1.Add(self.crack_passwd_btn, 0, 0, 0)
		self.SetSizer(grid_sizer_1)
		grid_sizer_1.AddGrowableCol(1)
		self.Layout()

		self.save_passwd_btn.Bind(wx.EVT_BUTTON, self.password_save)
		self.crack_passwd_btn.Bind(wx.EVT_BUTTON, self.password_crack)

	def password_save(self, event):
		passwd = self.passwd_entry.GetValue()
		hashfunction = md5
		h = hashfunction()
		h.update(passwd)
		self.hash_entry.SetValue(h.hexdigest())

	def password_crack(self, event):
		pass
