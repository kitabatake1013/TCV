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
import keymap

import constants
import errorCodes
import globalVars
import menuItemsStore

from logging import getLogger
import simpleDialog
from .base import *

import views.connect
import views.viewComment
import views.viewBroadcaster
import views.viewHistory
import views.viewFavorites
import views.accountManager
import webbrowser
import constants

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
		self.keymap=keymap.KeymapHandler(defaultKeymap.defaultKeymap)
		self.InstallMenuEvent(Menu(self.identifier),self.events.OnMenuSelect)
		self.createMainView(self.creator, self.keymap)

	def createMainView(self, viewCreator, keymap):
		self.commentListAcceleratorTable=keymap.GetTable("commentList")
		self.commentBodyAcceleratorTable=keymap.GetTable("commentBody")
		self.userInfoAcceleratorTable=keymap.GetTable("userInfo")
		self.commentList = viewCreator.ListCtrl(0, 0, style = wx.LC_REPORT, name = _("コメント一覧"))
		self.commentList.InsertColumn(0, _("名前"))
		self.commentList.InsertColumn(1, _("投稿"))
		self.commentList.InsertColumn(2, _("時刻"))
		self.commentList.InsertColumn(3, _("ユーザ名"))
		self.commentList.SetAcceleratorTable(self.commentListAcceleratorTable)
		self.selectAccount = viewCreator.combobox(_("コメント投稿アカウント"), [], None)
		self.commentBodyEdit, self.commentBodyStatic = viewCreator.inputbox(_("コメント内容"), 0, "", wx.TE_MULTILINE|wx.TE_DONTWRAP)
		self.commentBodyEdit.SetAcceleratorTable(self.commentBodyAcceleratorTable)
		self.commentSend = viewCreator.button(_("送信"), self.events.postComment)
		self.liveInfo = viewCreator.ListCtrl(0, 0, style = wx.LC_LIST, name = _("ライブ情報"))
		self.liveInfo.SetAcceleratorTable(self.userInfoAcceleratorTable)
		self.itemList = viewCreator.ListCtrl(0, 0, style = wx.LC_LIST, name = _("アイテム"))

class Menu(BaseMenu):
	def Apply(self,target):
		"""指定されたウィンドウに、メニューを適用する。"""

		#メニューの大項目を作る
		self.hFileMenu=wx.Menu()
		self.hPlayMenu=wx.Menu()
		self.hCommentMenu=wx.Menu()
		self.hLiveMenu=wx.Menu()
		self.hSettingsMenu=wx.Menu()
		self.hHelpMenu=wx.Menu()
		self.hCommentListContextMenu=wx.Menu()

		#メニューの中身
		#ファイルメニュー
		self.RegisterMenuCommand(self.hFileMenu,"connect",_("接続(&C) ..."))
		self.RegisterMenuCommand(self.hFileMenu,"viewHistory",_("最近接続したライブに接続(&H) ..."))
		self.RegisterMenuCommand(self.hFileMenu,"viewFavorites",_("お気に入りライブに接続(&F) ..."))
		self.RegisterMenuCommand(self.hFileMenu,"disconnect",_("切断(&D)"))
		self.RegisterMenuCommand(self.hFileMenu,"exit",_("終了(&Q)"))
		#再生メニュー
		self.RegisterMenuCommand(self.hPlayMenu,"play",_("再生(&P)"))
		self.RegisterMenuCommand(self.hPlayMenu,"stop",_("停止(&S)"))
		self.RegisterMenuCommand(self.hPlayMenu,"volumeUp",_("音量を上げる(&U)"))
		self.RegisterMenuCommand(self.hPlayMenu,"volumeDown",_("音量を下げる(&D)"))
		self.RegisterMenuCommand(self.hPlayMenu,"resetVolume",_("音量を１００％に設定(&R)"))
		#コメントメニュー
		self.RegisterMenuCommand(self.hCommentMenu,"viewComment",_("コメントの詳細を表示(&V) ..."))
		self.RegisterMenuCommand(self.hCommentMenu,"replyToSelectedComment",_("選択中のコメントに返信(&R)"))
		self.RegisterMenuCommand(self.hCommentMenu,"deleteSelectedComment",_("選択中のコメントを削除(&D)"))
		self.RegisterMenuCommand(self.hCommentMenu,"replyToBroadcaster",_("配信者に返信(&B)"))
		#ライブメニュー
		self.RegisterMenuCommand(self.hLiveMenu,"viewBroadcaster",_("配信者の情報を表示(&B) ..."))
		self.RegisterMenuCommand(self.hLiveMenu,"openLive",_("このライブをブラウザで開く(&O)"))
		self.RegisterMenuCommand(self.hLiveMenu,"addFavorites",_("お気に入りに追加(&A) ..."))
		#設定メニュー
		self.RegisterMenuCommand(self.hSettingsMenu,"basicSettings",_("基本設定(&G) ..."))
		self.RegisterMenuCommand(self.hSettingsMenu,"autoReadingSettings",_("自動読み上げの設定(&R) ..."))
		self.RegisterMenuCommand(self.hSettingsMenu,"accountManager",_("アカウントマネージャ(&M) ..."))
		#ヘルプメニュー
		self.RegisterMenuCommand(self.hHelpMenu,"versionInfo",_("バージョン情報(&V) ..."))
		self.RegisterMenuCommand(self.hHelpMenu,"viewErrorLog",_("エラーログを開く（開発用）"))

		#メニューバーの生成
		self.hMenuBar=wx.MenuBar()
		self.hMenuBar.Append(self.hFileMenu,_("ファイル(&F)"))
		self.hMenuBar.Append(self.hPlayMenu,_("再生(&P)"))
		self.hMenuBar.Append(self.hCommentMenu,_("コメント(&C)"))
		self.hMenuBar.Append(self.hLiveMenu,_("ライブ(&L)"))
		self.hMenuBar.Append(self.hSettingsMenu,_("設定(&S)"))
		self.hMenuBar.Append(self.hHelpMenu,_("ヘルプ(&H)"))
		target.SetMenuBar(self.hMenuBar)

class Events(BaseEvents):
	def OnMenuSelect(self,event):
		"""メニュー項目が選択されたときのイベントハンドら。"""
		#ショートカットキーが無効状態のときは何もしない
		if not self.parent.shortcutEnable:
			event.Skip()
			return

		selected=event.GetId()#メニュー識別しの数値が出る


		#終了
		if selected==menuItemsStore.getRef("exit"):
			self.Exit()
		#バージョン情報
		elif selected==menuItemsStore.getRef("versionInfo"):
			simpleDialog.dialog(_("バージョン情報"), _("%(appName)s Version %(versionNumber)s.\nCopyright (C) %(year)s %(developerName)s") %{"appName": constants.APP_NAME, "versionNumber": constants.APP_VERSION, "year":constants.APP_COPYRIGHT_YEAR, "developerName": constants.APP_DEVELOPERS})
		#接続
		elif selected==menuItemsStore.getRef("connect"):
			connectDialog = views.connect.Dialog()
			connectDialog.Initialize()
			ret = connectDialog.Show()
			if ret==wx.ID_CANCEL: return
			user = str(connectDialog.GetValue())
			if "https://twitcasting.tv/" in user:
				user = user[23:]
			elif "http://twitcasting.tv/" in user:
				user = user[22:]
			if "/" in user:
				user = user[0:user.find("/")]
			globalVars.app.Manager.connect(user)
			return
		#履歴
		elif selected==menuItemsStore.getRef("viewHistory"):
			if len(globalVars.app.Manager.history) == 0:
				simpleDialog.errorDialog(_("接続履歴がありません。"))
				return
			viewHistoryDialog = views.viewHistory.Dialog()
			viewHistoryDialog.Initialize()
			ret = viewHistoryDialog.Show()
			if ret==wx.ID_CANCEL: return
			globalVars.app.Manager.connect(globalVars.app.Manager.history[viewHistoryDialog.GetValue()])
			return
		#お気に入り
		elif selected==menuItemsStore.getRef("viewFavorites"):
			if len(globalVars.app.Manager.favorites) == 0:
				simpleDialog.errorDialog(_("お気に入りライブが登録されていません。"))
				return
			viewFavoritesDialog = views.viewFavorites.Dialog()
			viewFavoritesDialog.Initialize()
			ret = viewFavoritesDialog.Show()
			if ret==wx.ID_CANCEL: return
			globalVars.app.Manager.connect(globalVars.app.Manager.favorites[viewFavoritesDialog.GetValue()])
			return
		#コメントの詳細を表示
		elif selected==menuItemsStore.getRef("viewComment"):
			viewCommentDialog = views.viewComment.Dialog(globalVars.app.Manager.connection.comments[self.parent.commentList.GetFocusedItem()])
			viewCommentDialog.Initialize()
			viewCommentDialog.Show()
		#選択中のコメントに返信
		elif selected==menuItemsStore.getRef("replyToSelectedComment"):
			self.parent.commentBodyEdit.SetValue("@" + globalVars.app.Manager.connection.comments[self.parent.commentList.GetFocusedItem()]["from_user"]["screen_id"] + " ")
			self.parent.commentBodyEdit.SetInsertionPointEnd()
			self.parent.commentBodyEdit.SetFocus()
		#配信者に返信
		elif selected==menuItemsStore.getRef("replyToBroadcaster"):
			self.parent.commentBodyEdit.SetValue("@" + globalVars.app.Manager.connection.movieInfo["broadcaster"]["screen_id"] + " ")
			self.parent.commentBodyEdit.SetInsertionPointEnd()
			self.parent.commentBodyEdit.SetFocus()
		#コメントの削除
		elif selected==menuItemsStore.getRef("deleteSelectedComment"):
			dlg=simpleDialog.yesNoDialog(_("確認"),_("選択中のコメントを削除しますか？"))
			if dlg==wx.ID_NO:
				return
			globalVars.app.Manager.deleteComment()
		#お気に入りに追加
		elif selected==menuItemsStore.getRef("addFavorites"):
			if globalVars.app.Manager.connection.userId in globalVars.app.Manager.favorites:
				simpleDialog.errorDialog(_("すでに登録されています。"))
				return
			dlg=simpleDialog.yesNoDialog(_("確認"),_("%sのライブをお気に入りに追加しますか？") %(globalVars.app.Manager.connection.userId))
			if dlg==wx.ID_NO:
				return
			globalVars.app.Manager.addFavorites()
		#配信者の情報
		elif selected==menuItemsStore.getRef("viewBroadcaster"):
			viewBroadcasterDialog = views.viewBroadcaster.Dialog(globalVars.app.Manager.connection.movieInfo["broadcaster"])
			viewBroadcasterDialog.Initialize()
			viewBroadcasterDialog.Show()
		#ブラウザで開く
		elif selected==menuItemsStore.getRef("openLive"):
			webbrowser.open("http://twitcasting.tv/" + globalVars.app.Manager.connection.movieInfo["broadcaster"]["screen_id"])
		#アカウントマネージャ
		elif selected==menuItemsStore.getRef("accountManager"):
			accountManager = views.accountManager.Dialog([])
			accountManager.Initialize()
			accountManager.Show()
		#コメント送信（ホットキー）
		elif selected==menuItemsStore.getRef("postComment"):
			self.postComment(None)
		#再生
		elif selected==menuItemsStore.getRef("play"):
			globalVars.app.Manager.play()
		#停止
		elif selected==menuItemsStore.getRef("stop"):
			globalVars.app.Manager.stop()
		#音量を上げる
		elif selected==menuItemsStore.getRef("volumeUp"):
			globalVars.app.Manager.volumeUp()
		#音量を下げる
		elif selected==menuItemsStore.getRef("volumeDown"):
			globalVars.app.Manager.volumeDown()
		#音量のリセット
		elif selected==menuItemsStore.getRef("resetVolume"):
			globalVars.app.Manager.resetVolume()
		#エラーログを開く
		elif selected==menuItemsStore.getRef("viewErrorLog"):
			import subprocess
			subprocess.Popen(["start", ".\\errorLog.txt"], shell=True)
		#コメントリストのコンテキストメニューを開く
		elif selected==menuItemsStore.getRef("openCommentListContextMenu"):
			contextMenu = wx.Menu()
			self.parent.menu.RegisterMenuCommand(contextMenu,"replyToSelectedComment",_("選択中のコメントに返信(&R)"))
			urls = list(globalVars.app.Manager.connection.comments[self.parent.commentList.GetFocusedItem()]["urls"])
			for i, j in zip(urls, range(len(urls))):
				contextMenu.Append(constants.MENU_URL_FIRST + j, i.group())
			self.parent.hFrame.PopupMenu(contextMenu)
		#URLを開く
		elif selected >= constants.MENU_URL_FIRST:
			obj = event.GetEventObject()
			webbrowser.open(obj.GetLabel(selected))
		#ユーザー情報のコンテキストメニューを開く
		elif selected==menuItemsStore.getRef("openUserInfoContextMenu"):
			focusedItem = self.parent.liveInfo.GetFocusedItem()
			if focusedItem != self.parent.liveInfo.GetItemCount() - 1:
				return
			contextMenu = wx.Menu()
			self.parent.menu.RegisterMenuCommand(contextMenu,"replyToBroadcaster",_("配信者に返信(&B)"))
			self.parent.menu.RegisterMenuCommand(contextMenu,"viewBroadcaster",_("配信者の情報を表示(&B) ..."))
			self.parent.menu.RegisterMenuCommand(contextMenu,"addFavorites",_("お気に入りに追加(&A) ..."))
			self.parent.hFrame.PopupMenu(contextMenu)


	def postComment(self, event):
		commentBody = self.parent.commentBodyEdit.GetValue()
		result = globalVars.app.Manager.postComment(commentBody)
		if result == True:
			self.parent.commentBodyEdit.Clear()

	def Exit(self, event = None):
		for i in globalVars.app.Manager.timers:
			if i.IsRunning() == True:
				i.Stop()
		super().Exit()
