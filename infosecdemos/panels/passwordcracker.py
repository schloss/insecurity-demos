#!/usr/bin/env python

import wx

from hashlib import md5, sha1, sha224, sha256, sha384, sha512
import random

hashes = {
	"MD5": md5,
	"SHA1": sha1,
	"SHA256": sha256,
	"SHA512": sha512,
}


class PasswordCrackerPanel(wx.Panel):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent=parent)

		self.label_1 = wx.StaticText(self, -1, "Choose a password: ")
		self.passwd_entry = wx.TextCtrl(self, -1, "")
		self.save_passwd_btn = wx.Button(self, -1, "Save password")

		self.label_2 = wx.StaticText(self, -1, "Hashed password:")
		self.hash_entry = wx.TextCtrl(self, -1, "")
		self.crack_passwd_btn = wx.Button(self, -1, "Crack password")

		self.label_3 = wx.StaticText(self, -1, "Hashing function:")
		self.hash_select = wx.Choice(self, -1, choices=hashes.keys())
		self.salt_check = wx.CheckBox(self, -1, "Use salt?")
		self.label_5 = wx.StaticText(self, -1, "  Salt:")
		self.salt_choice = wx.TextCtrl(self, -1, "")
		self.label_5.Hide()
		self.salt_choice.Hide()

		grid_sizer_1 = wx.FlexGridSizer(4, 3, 0, 1)
		grid_sizer_1.Add(self.label_1, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
		grid_sizer_1.Add(self.passwd_entry, 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0)
		grid_sizer_1.Add(self.save_passwd_btn, 0, wx.ALIGN_CENTER_VERTICAL, 0)
		grid_sizer_1.Add(self.label_2, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
		grid_sizer_1.Add(self.hash_entry, 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0)
		grid_sizer_1.Add(self.crack_passwd_btn, 0, 0, 0)
		grid_sizer_1.Add(self.label_3, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer.Add(self.hash_select, 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0)
		sizer.Add(self.salt_check, 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0)
		sizer.Add(self.label_5, 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0)
		sizer.Add(self.salt_choice, 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0)
		grid_sizer_1.Add(sizer, 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0)
		sizer = wx.BoxSizer(wx.HORIZONTAL)
		grid_sizer_1.Add(sizer, 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0)
		self.SetSizer(grid_sizer_1)
		grid_sizer_1.AddGrowableCol(1)
		self.Layout()

		self.salt_check.Bind(wx.EVT_CHECKBOX, self.set_salt)
		self.save_passwd_btn.Bind(wx.EVT_BUTTON, self.password_save)
		self.crack_passwd_btn.Bind(wx.EVT_BUTTON, self.password_crack)

	def set_salt(self, event):
		if self.salt_check.IsChecked():
			salt = "%x" % random.getrandbits(32)
			self.salt_choice.SetValue(salt)
			self.label_5.Show()
			self.salt_choice.Show()
		else:
			self.salt_choice.SetEditable(False)
			self.label_5.Hide()
			self.salt_choice.Hide()
		self.Layout()

	def password_save(self, event):
		passwd = self.passwd_entry.GetValue()
		hashname = self.hash_select.GetItems()[self.hash_select.GetCurrentSelection()]
		hashfunction = hashes[hashname]
		h = hashfunction()
		h.update(passwd)
		self.hash_entry.SetValue(hashname + "$" + h.hexdigest())
		if self.salt_check.IsChecked():
			salt = self.salt_choice.GetValue()
			h.update(salt)
			self.hash_entry.SetValue(hashname + "$" + salt + "$" + h.hexdigest())

	def password_crack(self, event):
		pass
