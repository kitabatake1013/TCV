# -*- coding: utf-8 -*-
#Falcon Key-Value setting view base
#Copyright (C) 2020 yamahubuki <itiro.ishino@gmail.com>
#Note: All comments except these top lines will be written in Japanese. 

import wx

import globalVars
import constants
import keymap
import views.ViewCreator

from .baseDialog import *
from logging import getLogger
from simpleDialog import dialog

class KeyValueSettingDialogBase(BaseDialog):
	def __init__(self,identifier,settingDialog,columnInfo,*values):
		"""
			columnInfo:	(カラム名,フォーマット,width)のタプルのリスト(len>=2)
			*values:	{key:value}の辞書(len(values)=len(columnInfo)-1)
		"""
		super().__init__(identifier)
		if len(columnInfo)!=len(values)+1:
			raise ValueError(_("パラメータの個数が不正です。"))
		self.settingDialog=settingDialog
		self.columnInfo=columnInfo
		self.values=values
		self.columnNames=[]
		self.checkResultValueString=[("○","×")]*len(columnInfo)
		self.initialized=False

	def SetCheckResultValueString(self,column,t,f):
		assert not self.initialized		#Initialized()呼び出し後の変更は不可
		self.checkResultValueString[column]=(t,f)

	def Initialize(self,parent,title):
		super().Initialize(parent,title)
		self.InstallControls()
		return True
		self.initialized=True

	def InstallControls(self):
		"""いろんなwidgetを設置する。"""
		self.creator=views.ViewCreator.ViewCreator(self.viewMode,self.panel,self.sizer,wx.VERTICAL,20)
		self.hListCtrl, dammy=self.creator.listCtrl(_("現在の登録内容"), proportion=0, sizerFlag=wx.ALL|wx.ALIGN_CENTER_HORIZONTAL,size=(750,300),style=wx.LC_REPORT | wx.LC_NO_HEADER | wx.LC_SINGLE_SEL)

		for i,info in enumerate(self.columnInfo):
			self.hListCtrl.InsertColumn(i,info[0],format=info[1],width=info[2])
			self.columnNames.append(info[0])

		for key in self.values[0]:
			self._SetItem(-1,0,key)
			for i in range(0,len(self.values)):
				self._SetItem(-1,i+1,self.values[i][key])

		self.hListCtrl.Bind(wx.EVT_LIST_ITEM_SELECTED,self.ItemSelected)
		self.hListCtrl.Bind(wx.EVT_LIST_ITEM_DESELECTED,self.ItemSelected)

		#処理ボタン
		self.creator=views.ViewCreator.ViewCreator(self.viewMode,self.panel,self.creator.GetSizer(),wx.HORIZONTAL,20,"",wx.ALIGN_RIGHT)
		self.addButton=self.creator.button(_("追加"),self.add)
		self.editButton=self.creator.button(_("変更"),self.edit)
		self.editButton.Enable(False)
		self.deleteButton=self.creator.button(_("削除"),self.delete)
		self.deleteButton.Enable(False)

		#ボタンエリア
		self.creator=views.ViewCreator.ViewCreator(self.viewMode,self.panel,self.sizer,wx.HORIZONTAL,20,"",wx.ALIGN_RIGHT | wx.ALL,margin=20)
		self.bOk=self.creator.okbutton(_("ＯＫ"),self.OkButtonEvent)
		self.bCancel=self.creator.cancelbutton(_("キャンセル"),None)

	def ItemSelected(self,event):
		if self.hListCtrl.GetFocusedItem()<0:	#選択解除の通知
			self.editButton.Enable(False)
			self.deleteButton.Enable(False)
		else:									#選択追加の通知
			self.editButton.Enable(True)
			key=self.hListCtrl.GetItemText(self.hListCtrl.GetFocusedItem(),0)
			self.deleteButton.Enable(self.DeleteValidation(key))

	def DeleteValidation(self,key):
		"""
			指定されたキー(String)のデータを削除可能か否かを返す
			デフォルトではキーに関係なく削除可能なので、制限したい場合はオーバーライドする。
		"""
		return True

	def GetData(self):
		return self.values

	def add(self,event):
		d=self.settingDialog(self.wnd)
		d.Initialize()
		self.SettingDialogHook(d)
		if d.Show()==wx.ID_CANCEL:
			self.hListCtrl.SetFocus()
			return
		v=d.GetValue()
		if v[0] in self.values[0]:
			dlg=wx.MessageDialog(self.wnd,_("この%sは既に登録されています。登録を上書きしますか？") % self.columnNames[0],_("上書き確認"),wx.YES_NO|wx.ICON_QUESTION)
			if dlg.ShowModal()==wx.ID_NO:
				return
			index=self.hListCtrl.FindItem(-1,v[0])
			for i in range(0,len(self.values)):
				self._SetItem(index,i,v[i+1])
		else:
			for i in range(0,len(v)):
				self._SetItem(-1,i,v[i])
		for i in range(0,len(self.values)):
			self.values[i][v[0]]=v[i+1]
		self.hListCtrl.SetFocus()

	def edit(self,event):
		index=self.hListCtrl.GetFocusedItem()
		oldKey=self.hListCtrl.GetItemText(index,0)
		v=[None]*(len(self.values)+1)
		v[0]=oldKey
		for i in range(len(self.values)):
			v[i+1]=self.values[i][oldKey]

		d=self.settingDialog(self.wnd,*v)
		d.Initialize()
		self.SettingDialogHook(d)
		if d.Show()==wx.ID_CANCEL:
			self.hListCtrl.SetFocus()
			return
		v=d.GetValue()
		if oldKey!=v[0]:
			if v[0] in self.values[0]:
				dlg=wx.MessageDialog(self.wnd,_("この%sは既に登録されています。登録を上書きしますか？") % self.columnInfo[0][0],_("上書き確認"),wx.YES_NO|wx.ICON_QUESTION)
				if dlg.ShowModal()==wx.ID_NO:
					return

				#新たな名前で登録済みの行を削除する
				index2=self.hListCtrl.FindItem(-1,v[0])
				self.hListCtrl.DeleteItem(index2)
				if index>index2:		#削除によって１つずれた
					index-=1

			#古い名前で登録済みのデータを削除する
			for i in range(len(self.values)):
				del(self.values[i][oldKey])

		#新たなデータをビューに反映(古いデータに上書き)
		for i in range(len(v)):
			self._SetItem(index,i,v[i])

		#新たなデータを登録
		for i in range(len(self.values)):
			self.values[i][v[0]]=v[i+1]
		self.hListCtrl.SetFocus()

	def delete(self,event):
		index=self.hListCtrl.GetFocusedItem()
		key=self.hListCtrl.GetItemText(index,0)
		for i in range(len(self.values)):
			del self.values[i][key]
		self.hListCtrl.DeleteItem(index)
		self.hListCtrl.SetFocus()

	def _SetItem(self,index,column,data):
		"""
			画面上のリストを更新
			index=-1で末尾に追加
		"""
		if isinstance(data,bool):
			if data:
				data=self.checkResultValueString[column][0]
			else:
				data=self.checkResultValueString[column][1]
		print("%d,%d,%s" %(index,column,data))
		if index==-1:
			index=self.hListCtrl.GetItemCount()-1
			if column==0:
				return self.hListCtrl.InsertItem(index+1,data)
		return self.hListCtrl.SetItem(index,column,data)

	def SettingDialogHook(self,dialog):
		"""
			settingDialogのInitializeが終わったあと、表示の直前に呼ばれる
			オーバーライドすることでダイアログへの値の受け渡しなどに活用できる
		"""
		pass

	def OkButtonEvent(self,event):
		"""
			最終的な値のバリデーションを行いたい場合にオーバーライドする。
		"""
		event.Skip()


class SettingDialogBase(BaseDialog):
	"""Dialogの上に作られ、設定内容を入力するダイアログ"""

	def __init__(self,parent,valueNames,buttons,*v):
		"""
			valueNamesには各入力欄の名前(「名前」「パス」「ショートカットキー」など)とユーザによる直接入力の可否のタプルのリストを指定。
			直接入力の可否はTrue/Falseの他、Noneにすると非表示にもできる。非表示でも入力欄自体は存在する為、内部用の値の保持に使える。
			buttonsには、設置するボタンの情報をNone(ボタン無)または("参照",self.getRef())のように名前と押された時の動作関数のタプルで定義したもののリストを指定
			*vには各入力欄の初期値(空欄を省略可能)

		"""
		super().__init__("valueSettingDialog")
		if len(valueNames)!=len(v):
			raise ValueError(_("項目名と初期値の指定件数が一致しません。"))
		self.parent=parent
		self.valueNames=valueNames
		self.buttons=buttons
		self.values=list(v)
		self.edits=[None]*len(self.valueNames)

	def Initialize(self,title):
		super().Initialize(self.parent,title,style=wx.WS_EX_VALIDATE_RECURSIVELY|wx.DEFAULT_FRAME_STYLE)
		self.InstallControls()
		return True

	def InstallControls(self):
		"""いろんなwidgetを設置する。"""
		self.baseCreator=views.ViewCreator.ViewCreator(self.viewMode,self.panel,self.sizer,wx.VERTICAL,20)

		for i,name in enumerate(self.valueNames):
			self.creator=views.ViewCreator.ViewCreator(self.viewMode,self.baseCreator.GetPanel(),self.baseCreator.GetSizer(),wx.HORIZONTAL,10)
			if type(name[1])==str:
				self.edits[i]=self.creator.checkbox(name[1],state=self.values[i], x=500)
			elif name[1]:
				self.edits[i],dummy=self.creator.inputbox(name[0],x=500,defaultValue=self.values[i], textLayout=wx.VERTICAL)
			else:
				self.edits[i],dummy=self.creator.inputbox(name[0],x=500,defaultValue=self.values[i],style=wx.TE_READONLY, textLayout=wx.VERTICAL)
			if name[1]==None:
				self.edits[i].GetParent().Hide()
			if self.buttons[i]:
				dummy=self.creator.button(self.buttons[i][0],self.buttons[i][1],sizerFlag=wx.ALIGN_BOTTOM | wx.BOTTOM, margin=10)

		#ボタンエリア
		self.creator=views.ViewCreator.ViewCreator(self.viewMode,self.panel,self.sizer,wx.HORIZONTAL,20,"",wx.ALIGN_RIGHT|wx.TOP, 10)
		self.bOk=self.creator.okbutton(_("ＯＫ"),self.OkButtonEvent)
		self.bCancel=self.creator.cancelbutton(_("キャンセル"),None)

	def GetData(self):
		ret=[None]*len(self.edits)
		for i in range(len(self.edits)):
			if isinstance(self.edits[i],wx.CheckBox):
				ret[i]=self.edits[i].GetValue()
			else:
				ret[i]=self.edits[i].GetLineText(0)
		ret[0]=ret[0].lower()			#iniファイルへの保存の為キーは小文字に統一
		return ret

	def OkButtonEvent(self,event):
		"""
			OKボタン押下時のイベント処理。
			iniファイル保存時のキーとなる先頭要素が空欄でないか、半角の=を含んでいないかバリデーションする。
			問題なければValidation()を呼び出す。
		"""
		key=self.edits[0].GetLineText(0)
		if key=="" or "=" in key:
			dialog(_("エラー"),_("%sを空白や半角の=を含む値に設定することはできません。") % self.valueNames[0][0])
			return
		return self.Validation(event)

	def Validation(self,event):
		"""
			入力値のバリデーションをしたい場合にオーバーライドする。
			そのままreturnすれば拒否でき、event.Skip()すれば許可できる。
			デフォルトでは何も検査せず許可している。
		"""
		event.Skip()


def KeySettingValidation(oldKeyConfig,newKeyConfig,logger,entries=None,AllowNewKeyDuplication=False):
	"""
		oldKeyConfig:	{name:key}	設定変更前
		newKeyConfig:	{name:key}	設定変更後
		logger:			logger		エラー時のログ出力用
		entries:		set(keymap.AcceleratorEntry)	重複判定対象(省略時はメインビューのみ)
		AllowNewKeyDuplication	bool	newKey内での重複を許すならTrue
	"""
	if logger==None:
		logger=getLogger("%s.%s" % (constants.LOG_PREFIX,"KeySettingValidation"))
	errors=""
	oldKeys={}
	for k,vs in oldKeyConfig.items():
		for v in vs.split("/"):
			oldKeys.setdefault(v, list()).append(k)
	newKeys={}
	for k,vs in newKeyConfig.items():
		for v in vs.split("/"):
			newKeys.setdefault(v, list()).append(k)
	if entries==None:
		entries=globalVars.app.hMainView.GetKeyEntries()

	for k,v in newKeys.items():
		if k==_("なし"):
			continue
		if not AllowNewKeyDuplication:
			if len(v)==2:
				errors+=_("%sと%sに同じショートカットキー%sが設定されています。\n") % (v[0],v[1],k)
				continue
			elif len(v)>2:
				errors+=_("%s、%sなど計%d箇所に同じショートカットキー%sが設定されています。\n") % (v[0],v[1],len(v),k)
				continue
		e=keymap.makeEntry("DUMMY",k,None,logger)
		if e==None:
			errors+=_("設定されたショートカット%sが認識できません。お手数ですが、このエラーメッセージを作者へご連絡ください。\n") % k
		elif e in entries and (k not in oldKeys):
			errors+=_("%sに設定されたショートカットキー%sは、別の場所で利用されています。\n") % (v[0],k)
	if errors!="":
		dialog(_("エラー"),errors)
		return False
	return True
