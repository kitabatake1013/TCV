﻿# -*- coding: utf-8 -*-
#main view
#Copyright (C) 2019 Yukio Nozawa <personal@nyanchangames.com>
#Copyright (C) 2019-2020 yamahubuki <itiro.ishino@gmail.com>

import logging
import os
import sys
import wx
import re
import ctypes
import pywintypes

import constants
import errorCodes
import globalVars
import menuItemsStore

from logging import getLogger
from simpleDialog import dialog
from .base import *
from simpleDialog import *

import views.connect
import views.viewItem

class MainView(BaseView):
	def __init__(self):
		super().__init__()
		self.identifier="mainView"#このビューを表す文字列
		self.log=getLogger(self.identifier)
		self.log.debug("created")
		self.app=globalVars.app
		self.events=Events(self,self.identifier)
		title=constants.APP_NAME
		super().Initialize(
			title,
			self.app.config.getint(self.identifier,"sizeX",800),
			self.app.config.getint(self.identifier,"sizeY",600),
			self.app.config.getint(self.identifier,"positionX"),
			self.app.config.getint(self.identifier,"positionY")
		)
		self.InstallMenuEvent(Menu(self.identifier),self.events.OnMenuSelect)
		self.commentList = self.creator.ListCtrl(0, 0, style = wx.LC_REPORT, name = _("コメント一覧"))
		self.commentList.InsertColumn(0, _("名前"))
		self.commentList.InsertColumn(1, _("投稿"))
		self.commentList.InsertColumn(2, _("時刻"))
		self.commentList.InsertColumn(3, _("ユーザ名"))
		self.selectAccount = self.creator.combobox(_("コメント投稿アカウント"), [], None)
		self.commentBodyEdit, self.commentBodyStatic = self.creator.inputbox(_("コメント内容"))
		self.commentSend = self.creator.button(_("送信"), self.events.postComment)
		self.liveInfo = self.creator.ListCtrl(0, 0, style = wx.LC_LIST, name = _("ライブ情報"))

class Menu(BaseMenu):
	def Apply(self,target):
		"""指定されたウィンドウに、メニューを適用する。"""

		#メニューの大項目を作る
		self.FileMenu=wx.Menu()
		self.PlayMenu=wx.Menu()
		self.CommentMenu=wx.Menu()
		self.SettingsMenu=wx.Menu()
		self.HelpMenu=wx.Menu()

		#メニューの中身
		#ファイルメニュー
		self.RegisterMenuCommand(self.FileMenu,"connect",_("接続(&C) ..."))
		self.RegisterMenuCommand(self.FileMenu,"disconnect",_("切断(&D)"))
		self.RegisterMenuCommand(self.FileMenu,"exit",_("終了(&Q)"))
		#再生メニュー
		self.RegisterMenuCommand(self.PlayMenu,"play",_("再生(&P)"))
		self.RegisterMenuCommand(self.PlayMenu,"stop",_("停止(&S)"))
		self.RegisterMenuCommand(self.PlayMenu,"volumeUp",_("音量を上げる(&U)"))
		self.RegisterMenuCommand(self.PlayMenu,"volumeDown",_("音量を下げる(&D)"))
		#コメントメニュー
		self.RegisterMenuCommand(self.CommentMenu,"viewItem",_("コメントの詳細を表示(&V) ..."))
		self.RegisterMenuCommand(self.CommentMenu,"reply",_("投稿者に返信(&R)"))
		self.RegisterMenuCommand(self.CommentMenu,"delete",_("選択中のコメントを削除(&D)"))
		#設定メニュー
		self.RegisterMenuCommand(self.SettingsMenu,"basicSettings",_("基本設定(&G) ..."))
		self.RegisterMenuCommand(self.SettingsMenu,"autoReadingSettings",_("自動読み上げの設定(&R) ..."))
		self.RegisterMenuCommand(self.SettingsMenu,"manageAccounts",_("アカウントの管理(&M) ..."))
		#ヘルプメニュー
		self.RegisterMenuCommand(self.HelpMenu,"versionInfo",_("バージョン情報(&V) ..."))

		#メニューバーの生成
		self.hMenuBar=wx.MenuBar()
		self.hMenuBar.Append(self.FileMenu,_("ファイル(&F)"))
		self.hMenuBar.Append(self.PlayMenu,_("再生(&P)"))
		self.hMenuBar.Append(self.CommentMenu,_("コメント(&C)"))
		self.hMenuBar.Append(self.SettingsMenu,_("設定(&S)"))
		self.hMenuBar.Append(self.HelpMenu,_("ヘルプ(&H)"))
		target.SetMenuBar(self.hMenuBar)

class Events(BaseEvents):
	def OnMenuSelect(self,event):
		"""メニュー項目が選択されたときのイベントハンドら。"""
		#ショートカットキーが無効状態のときは何もしない
		if not self.parent.shortcutEnable:
			event.Skip()
			return

		selected=event.GetId()#メニュー識別しの数値が出る


		if selected==menuItemsStore.getRef("exit"):
			self.Exit()
		elif selected==menuItemsStore.getRef("versionInfo"):
			dialog(_("バージョン情報"), _("%(appName)s Version %(versionNumber)s.\nCopyright (C) %(year)s %(developerName)s") %{"appName": constants.APP_NAME, "versionNumber": constants.APP_VERSION, "year":constants.APP_COPYRIGHT_YEAR, "developerName": constants.APP_DEVELOPERS})
		elif selected==menuItemsStore.getRef("connect"):
			connectDialog = views.connect.Dialog()
			connectDialog.Initialize()
			ret = connectDialog.Show()
			if ret==wx.ID_CANCEL: return
			globalVars.app.Manager.connect(str(connectDialog.GetValue()))
			return
		elif selected==menuItemsStore.getRef("viewItem"):
			viewItemDialog = views.viewItem.Dialog(globalVars.app.Manager.connection.comments[self.parent.commentList.GetFocusedItem()])
			viewItemDialog.Initialize()
			ret = viewItemDialog.Show()

	def postComment(self, event):
		commentBody = self.parent.commentBodyEdit.GetLineText(0)
		result = globalVars.app.Manager.postComment(commentBody)
		if result == True:
			self.parent.commentBodyEdit.Clear()
