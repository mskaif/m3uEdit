#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys
import pandas as pd
from PyQt5.QtCore import Qt, QDir, QAbstractTableModel, QModelIndex, QVariant
from PyQt5.QtWidgets import (QMainWindow, QTableView, QApplication, 
                             QFileDialog, QAbstractItemView, QMessageBox)
from PyQt5.QtGui import QStandardItem, QIcon, QKeySequence

class PandasModel(QAbstractTableModel):
    def __init__(self, df = pd.DataFrame(), parent=None): 
        QAbstractTableModel.__init__(self, parent=None)
        self._df = df
        self.setChanged = False
        self.dataChanged.connect(self.setModified)

    def setModified(self):
        self.setChanged = True
        print(self.setChanged)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return QVariant()
        if orientation == Qt.Horizontal:
            try:
                return self._df.columns.tolist()[section]
            except (IndexError, ):
                return QVariant()
        elif orientation == Qt.Vertical:
            try:
                return self._df.index.tolist()[section]
            except (IndexError, ):
                return QVariant()

    def flags(self, index):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid():
            if (role == Qt.EditRole):
                return self._df.values[index.row()][index.column()]
            elif (role == Qt.DisplayRole):
                return self._df.values[index.row()][index.column()]
        return None

    def setData(self, index, value, role):
        row = self._df.index[index.row()]
        col = self._df.columns[index.column()]
        self._df.values[row][col] = value
        self.dataChanged.emit(index, index)
        return True

    def rowCount(self, parent=QModelIndex()): 
        return len(self._df.index)

    def columnCount(self, parent=QModelIndex()): 
        return len(self._df.columns)

    def sort(self, column, order):
        colname = self._df.columns.tolist()[column]
        self.layoutAboutToBeChanged.emit()
        self._df.sort_values(colname, ascending= order == Qt.AscendingOrder, inplace=True)
        self._df.reset_index(inplace=True, drop=True)
        self.layoutChanged.emit()

class Viewer(QMainWindow):
    def __init__(self, parent=None):
      super(Viewer, self).__init__(parent)
      self.filename = ""
      self.fname = ""
      self.csv_file = ""
      self.m3u_file = ""
      self.setGeometry(0, 0, 1000, 600)
      self.lb = QTableView()
      self.lb.horizontalHeader().hide()
      self.model =  PandasModel()
      self.lb.setModel(self.model)
      self.lb.setEditTriggers(QAbstractItemView.DoubleClicked)
      self.lb.setSelectionBehavior(self.lb.SelectRows)
      self.lb.setSelectionMode(self.lb.SingleSelection)
      self.setStyleSheet(stylesheet(self))
      self.lb.setAcceptDrops(True)
      self.setCentralWidget(self.lb)
      self.setContentsMargins(10, 10, 10, 10)
      self.statusBar().showMessage("Ready", 0)
      self.setWindowTitle("m3u Editor")
      self.setWindowIcon(QIcon.fromTheme("multimedia-playlist"))
      self.createMenuBar()
      self.lb.setFocus()
      
    def convert_to_csv(self):
        mylist = open(self.m3u_file, 'r').read().splitlines()

        headers = ['tvg-name', 'group-title', 'tvg-logo', 'tvg-id', 'url']
        group = ""
        ch = ""
        url = ""
        id = ""
        logo = ""
        csv_content = ""
        csv_content += '\t'.join(headers)
        csv_content += "\n"
        for x in range(1, len(mylist)-1):
            line = mylist[x]
            nextline = mylist[x+1]
            if line.startswith("#EXTINF") and not "**********" in line:
                if 'tvg-name="' in line:
                    ch = line.partition('tvg-name="')[2].partition('"')[0]
                elif 'tvg-name=' in line:
                    ch = line.partition('tvg-name=')[2].partition(' tvg')[0]
                else:
                    ch = line.rpartition(',')[2]        
                if ch == "":
                    ch = "No Name"
                ch = ch.replace('"', '')
                    
                if 'group-title="' in line:
                    group = line.partition('group-title="')[2].partition('"')[0]

                elif "group-title=" in line:
                    group = line.partition('group-title=')[2].partition(' tvg')[0]
                else:
                    group = "TV"
                group = group.replace('"', '')        
                
                if 'tvg-id="' in line:
                    id = line.partition('tvg-id="')[2].partition('"')[0]
                elif 'tvg-id=' in line:
                    id = line.partition('tvg-id=')[2].partition(' ')[0]
                else:
                    id = ""
                id = id.replace('"', '')
                
                url = nextline
                if 'tvg-logo="' in line:
                    logo = line.partition('tvg-logo="')[2].partition('"')[0]
                elif 'tvg-logo=' in line:
                    logo = line.partition('tvg-logo=')[2].partition(' ')[0]        
                else:
                    logo = ""            
                csv_content += (f'{ch}\t{group}\t{logo}\t{id}\t{url}\n')
        self.fname = self.m3u_file.rpartition("/")[2].replace(".m3u", ".csv")
        self.csv_file = f'/tmp/{self.fname}'
        with open(self.csv_file, 'w') as f:        
            f.write(csv_content)

    def closeEvent(self, event):
        print(self.model.setChanged)
        if  self.model.setChanged == True:
            quit_msg = "<b>The document was changed.<br>Do you want to save the changes?</ b>"
            reply = QMessageBox.question(self, 'Save Confirmation', 
                     quit_msg, QMessageBox.Yes, QMessageBox.No)
            if reply == QMessageBox.Yes:
                event.accept()
                self.writeCSV()
        else:
            print("nothing changed. goodbye")

    def createMenuBar(self):
        bar=self.menuBar()
        self.filemenu=bar.addMenu("File")
        self.separatorAct = self.filemenu.addSeparator()
        self.filemenu.addAction(QIcon.fromTheme("document-open"), "Load M3U",  self.loadM3U, QKeySequence.Open) 
        self.filemenu.addAction(QIcon.fromTheme("document-save-as"), "Save as ...",  self.writeCSV, QKeySequence.SaveAs) 

    def openFile(self, path=None):
        path, _ = QFileDialog.getOpenFileName(self, "Open File", QDir.homePath() + "/Dokumente/TV/","Playlists (*.m3u)")
        if path:
            return path

    def loadM3U(self):
        fileName = self.openFile()
        if fileName:
            self.m3u_file = fileName
            self.convert_to_csv()
            print(fileName + " loaded")
            f = open(self.csv_file, 'r+b')
            with f:
                self.filename = fileName
                df = pd.read_csv(f, delimiter = '\t', keep_default_na = False, low_memory=False, header=None)
                self.model = PandasModel(df)
                self.lb.setModel(self.model)
                #self.model.setHeaderData(0, Qt.Horizontal, 'tvg-name', Qt.DisplayRole)  
                self.lb.resizeColumnsToContents()
                self.lb.selectRow(0)
                self.statusBar().showMessage(f"{fileName} loaded", 0)
                self.model.setChanged = False
                self.lb.verticalHeader().setMinimumWidth(24)
             

    def writeCSV(self):
        fileName, _ = QFileDialog.getSaveFileName(self, "Save File", self.fname.replace(".csv", ".m3u"),"M3U Files (*.m3u)")
        if fileName:
            # save temporary csv
            f = open(self.csv_file, 'w')
            newModel = self.model
            dataFrame = newModel._df.copy()
            dataFrame.to_csv(f, sep='\t', index = False, header = False)  
            f.close()
            
            # convert to m3u
            mylist = open(self.csv_file, 'r').read().splitlines()
            group = ""
            ch = ""
            url = ""
            id = ""
            logo = ""
            m3u_content = ""

            headers = ['tvg-name', 'group-title', 'tvg-logo', 'tvg-id', 'url']
            m3u_content += "#EXTM3U\n"

            for x in range(1, len(mylist)):
                line = mylist[x].split('\t')
                ch = line[0]
                group = line[1]
                logo = line[2]
                id = line[3]
                url = line[4]
                
                m3u_content += f'#EXTINF:-1 tvg-name="{ch}" group-title="{group}" tvg-logo="{logo}" tvg-id="{id}",{ch}\n{url}\n'

            with open(fileName, 'w') as f:        
                f.write(m3u_content)

            print(fileName + " saved")
            self.model.setChanged = False


    def writeCSV_update(self):
        quit_msg = "<b>The document was changed.<br>Do you want to save the changes?</ b>"
        reply = QMessageBox.question(self, 'Save Confirmation', 
                 quit_msg, QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()
            if self.filename:
                print(self.filename + " saved")
                f = open(self.filename, 'w')
                newModel = self.model
                dataFrame = newModel._df.copy()
                dataFrame.to_csv(f, sep='\t', index = False, header = False)
        else:
            print("not saved, goodbye ...")
            return

def stylesheet(self):
        return """
    QMenuBar
        {
            background: transparent;
            border: 0px;
        }
        
    QMenuBar:hover
        {
            background: #d3d7cf;
        }
        
    QTableView
        {
            border: 1px solid #d3d7cf;
            border-radius: 0px;
            font-size: 8pt;
            background: #eeeeec;
            selection-color: #ffffff
        }
    QTableView::item:hover
        {   
            color: black;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 #729fcf, stop:1 #d3d7cf);           
        }
        
    QTableView::item:selected {
            color: #F4F4F4;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 #6169e1, stop:1 #3465a4);
        } 

    QTableView QTableCornerButton::section {
            background: #D6D1D1;
            border: 0px outset black;
        }
        
    QHeaderView:section {
            background: #d3d7cf;
            color: #555753;
            font-size: 8pt;
        }
        
    QHeaderView:section:checked {
            background: #204a87;
            color: #ffffff;
        }
        
    QStatusBar
        {
        font-size: 7pt;
        color: #555753;
        }
        
    """
 
if __name__ == "__main__":
 
    app = QApplication(sys.argv)
    main = Viewer()
    main.show()
sys.exit(app.exec_())