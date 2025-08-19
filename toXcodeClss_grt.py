# -*- coding: utf-8 -*-
# MySQL Workbench module
# conversor de MySQL a Cloudkit
# Written in MySQL Workbench 8.0.29

import re
import io

import grt
import mforms

from wb import DefineModule, wbinputs
from workbench.ui import WizardForm, WizardPage
from mforms import newButton, newCodeEditor, FileChooser

ModuleInfo = DefineModule(name="toXcodeClss",author="Jose Uzcategui",version="1.1" )

@ModuleInfo.plugin("wb.util.toXcodClss",
                   caption="To XcodeClss",
                   input=[wbinputs.currentCatalog()],
                   groups=["Catalog/Utilities", "Menu/Catalog"])

@ModuleInfo.export(grt.INT,grt.classes.db_Catalog)

def toXcodeClss(cat):
    txt = io.StringIO()

    txt.write(Header())

    catlg = grt.root.wb.doc.physicalModels[0].catalog
    getSchema(txt,catlg)

    sql_text = txt.getvalue()
    txt.close()

    wizard = ExportCloudkitWizard(sql_text)
    wizard.run()

    return 0
    
def Header():
    major = str(grt.root.wb.info.version.majorNumber)
    minor = str(grt.root.wb.info.version.minorNumber)
    reles = str(grt.root.wb.info.version.releaseNumber)
    versn = str(ModuleInfo.version)
    autho = str(grt.root.wb.doc.info.author)
    captn = str(grt.root.wb.doc.info.caption)
    projt = str(grt.root.wb.doc.info.project)
    fchgn = str(grt.root.wb.doc.info.dateChanged)
    fcrea = str(grt.root.wb.doc.info.dateCreated)
    dscrp = str(grt.root.wb.doc.info.description)
    global newln 
    newln = "\n"
    line1 = "// Creator:\tMySQL Workbench {1}.{2}.{3}/ExportCloudkit Plugin {4} {0}// Author:\t{5} {0}// Caption:\t{6} {0}// Project:\t{7} {0}// Changed:\t{8} {0}// Created:\t{9} {0}// Description:\t{10} {0} ".format(newln,major,minor,reles,versn,autho,captn,projt,fchgn,fcrea,dscrp)

    return line1

def getSchema(txt,cat):
    for schema in cat.schemata:
        for table in schema.tables:
            txt.write("{0}// MARK: - {1} {0}".format(newln,table.comment))
            txt.write("{0}/// {1} {0}".format(newln,table.comment))
            txt.write("\t struct  {1} {{ {0}".format(newln,table.name))
            crearVARvariables(txt,table)
            crearINI(txt,table)
            crearINIvariables(txt,table)
            crearINIrecord(txt,table)
            crearecordINI(txt,table)
            txt.write("}")


# Function to verify datatype -------------------!
def convertDataType(datatype):
    ret = "String"
    if "Int".upper() in datatype.upper():
        ret = "Int"
    elif datatype.upper() in ["Real".upper(),"Double".upper()]:
        ret = "Double"
    elif datatype.upper() in ["Date".upper(),"Time".upper(),"dateTime".upper()]:
        ret = "Date"
    else:
        ret = "String"
    return ret

# Function to get column Info ------------------!
def crearVARvariables(txt,tableInfo):
    clavesforaneas = []
    for fkey in tableInfo.foreignKeys:
        for cols in fkey.columns:
            clavesforaneas.append(cols.name)
    for column in tableInfo.columns :
        colName = column.name
        colComn = column.comment.strip() if column.comment.strip() != "" else "Falta descripcion"
        colTipo = convertDataType(column.simpleType.name)
        if colName in clavesforaneas:
            colComn = "REFERENCE \n " + colComn  
        if "\n" in colComn:
            colArry = ['/// {0}'.format(element) for element in colComn.split(newln)]
            #txt.write(str(colArry)) 
            colComn = newln.join(colArry)
            txt.write("\t\t {0} {1}".format(colComn,newln)) 
        else:
            txt.write("\t\t ///{0} {1}".format(colComn,newln))  
        txt.write("\t\t var {0} : {1} {2}".format(colName,colTipo,newln)) 

# Function to verify datatype -------------------!
def convertDataValue(datatype):
    ret = "\"\""
    if "Int".upper() in datatype.upper():
        ret = "Int.zero"
    elif datatype.upper() in ["Real".upper(),"Double".upper()]:
        ret = "Double.zero"
    elif datatype.upper() in ["Date".upper(),"Time".upper(),"dateTime".upper()]:
        ret = " DateFormatter().date(from: \"0001-01-01 01:01:01\") ?? Date() "
    return ret

# Function to create INIT() ------------------!
def crearINI(txt,tableInfo):
    txt.write("\n init() { \n ")
    for column in tableInfo.columns :
        colName = column.name
        colVal = convertDataValue(column.simpleType.name)
        txt.write("\t\t self.{0} = {1} {2}".format(colName,colVal,newln)) 
    txt.write("} \n")

# Function to create INIT(campo1: tipo ... ) ------------------!
def crearINIvariables(txt,tableInfo):
    varentrad = []
    for column in tableInfo.columns :
        colName = column.name
        colTipo = convertDataType(column.simpleType.name)
        varentrad.append(" {0} : {1}".format(colName,colTipo))
    entrad = ",".join(varentrad)
    txt.write("{1} init ( {0} ) {{ {1}".format(entrad,newln)) 
    for column in tableInfo.columns :
        colName = column.name
        txt.write(" self.{0} = {0} {1}".format(colName,newln)) 
    txt.write("} \n")

# Function to create INIT desde CKrecord ------------------!
def crearINIrecord(txt,tableInfo):
    txt.write("\n  init(record: CKRecord) { \n ") 
    for column in tableInfo.columns :
        colName = column.name
        colTipo = convertDataType(column.simpleType.name)
        colVal = convertDataValue(column.simpleType.name)
        txt.write(" self.{0} = record[\"{0}\"] as? {1} ?? {2} {3}".format(colName,colTipo,colVal,newln)) 
    txt.write("} \n")

# Function to create  CKrecord desde INIT------------------!
def crearecordINI(txt,tableInfo):
    txt.write("\n/// Funcion para crear un CKRecord de {0} \n".format(tableInfo.name)) 
    txt.write(" func toCKRecord() -> CKRecord {{ \n let record = CKRecord(recordType: \"{0}\") \n".format(tableInfo.name)) 
    for column in tableInfo.columns :
        colName = column.name
        txt.write(" record[\"{0}\"] = {0} {1}".format(colName,newln)) 
    txt.write("return record \n } \n")

class ExportCloudkitWizard_PreviewPage(WizardPage):
    def __init__(self, owner, sql_text):
        WizardPage.__init__(self, owner, "Review Generated Script")

        self.save_button = mforms.newButton()
        self.save_button.enable_internal_padding(True)
        self.save_button.set_text("Save to File...")
        self.save_button.set_tooltip("Save the text to a new file.")
        self.save_button.add_clicked_callback(self.save_clicked)

        self.copy_button = mforms.newButton()
        self.copy_button.enable_internal_padding(True)
        self.copy_button.set_text("Copy to Clipboard")
        self.copy_button.set_tooltip("Copy the text to the clipboard.")
        self.copy_button.add_clicked_callback(self.copy_clicked)

        self.sql_text = mforms.newCodeEditor()
        self.sql_text.set_language(mforms.LanguageMySQL)
        self.sql_text.set_text(sql_text)

    def go_cancel(self):
        self.main.finish()

    def create_ui(self):
        # buttons for copy to clipboard and save to file are located into button_box
        button_box = mforms.newBox(True)
        button_box.set_padding(8)
        button_box.set_spacing(8)

        button_box.add(self.save_button, False, True)
        button_box.add(self.copy_button, False, True)

        self.content.add_end(button_box, False, True)
        self.content.add_end(self.sql_text, True, True)

    def save_clicked(self):
        file_chooser = mforms.newFileChooser(self.main, mforms.SaveFile)
        file_chooser.set_extensions('SQL Files (*.sql)|*.sql', 'sql')
        if file_chooser.run_modal() == mforms.ResultOk:
            path = file_chooser.get_path()
            text = self.sql_text.get_text(False)
            try:
                with open(path, 'w+') as f:
                    f.write(text)
            except Exception as e:
                mforms.Utilities.show_error(
                    'Save to File',
                    'Could not save to file "%s": %s' % (path, str(e)),
                    "OK")

    def copy_clicked(self):
        mforms.Utilities.set_clipboard_text(self.sql_text.get_text(False))

class ExportCloudkitWizard(WizardForm):
    def __init__(self, sql_text):
        WizardForm.__init__(self, None)

        self.set_name("Cloudkit_export_wizard")
        self.set_title("Cloudkit Export Wizard")

        self.preview_page = ExportCloudkitWizard_PreviewPage(self, sql_text)
        self.add_page(self.preview_page)