# -*- coding: utf-8 -*-
"""
Created on Sat Nov 18 23:06:03 2023

@author: mohammed.omari
"""

import pandas as pd
from copy import deepcopy
import os,shutil,subprocess
import time
from aux_functions import progress_bar,File,os_cmd
import numpy as np



Warning=print
# *****************************************************************************
"""

"""
# *****************************************************************************

class flag:
    """
    This class is amined to define linkage flag for search and replace 

    """
    def __init__(self,name,attribute,Format=None,**kwd):
        self.name=name
        self.attribute=attribute
        self.format = Format
        self.value = None
        pass
    def __call__(self,val):
        self.set_value(val)
        if self.value is None:
            self.value = "BINGO-->>>NEED TO MODIFY THE CODE"
        return self.format%self.value if self.format is not None else self.value
    def set_value(self,val):
        self.value=val
        return self
    def reset(self):
        self.value=None
        return self
    def get_value(self):
        if self.value is None:
            return None
        #print("BINGO>>>>>>>>",self.value,self.name,self.attribute)
        return self.format%self.value if self.format is not None else self.value
    def __kwargs_hanlder(self,**kwd):
        for item,val in kwd.items():
            if item in self.__dict__:
                self.__setattr__(item, val)
            pass
        


class Flags:
    """
    This class process set of flags class 

    """
    def __init__(self):
        self.__flags__={}
    def add_flag(self,*flags):
        for f in flags:
            if not isinstance(f, flag):
                Warning("Bad Flag")
                return self
            self.__flags__[f.name]=f
        return self
    def __setitem__(self,item,val):
        if item!=val.name:
            Warning("Bad flag name:class")
        self.__flags__[item]=val
    
    def __len__(self):
        return len(self.__flags__)
    
    def __getitem__(self,item):
        return self.__flags__[item]
    
    def __iter__(self):
        self.current_index = 0
        self.__ks = list(self.__flags__.keys())
        return self
    def __next__(self):
        if self.current_index < len(self):
            self.current_index += 1
            return self[self.__ks[self.current_index-1]]
        del self.current_index,self.__ks
        raise StopIteration        
    def set_values_from_attriutes(self,att_vals):
        for att,val in att_vals.items():
            for f,f_class in self.__flags__.items():
                if f_class.attribute == att:
                    f_class.set_value(val)
                    break
        return self
    def get_flags_values(self,att_vals=None):
        if att_vals is not None:
            self.set_values_from_attriutes(att_vals)
        return {f:f_class.get_value() for f,f_class in self.__flags__.items()}
    def __kwargs_hanlder(self,**kwd):
        for item,val in kwd.items():
            if item in self.__dict__:
                self.__setattr__(item, val)
            pass
class Case:
    """
    This class is for define the multi-run case infromation. it needs at least
    proiding it the database of the sampling, the flags map, the input files te
    """
    def __init__(self,name="",
                 db=pd.DataFrame(),
                 attributes=[],
                 FlagsMap={},
                 exe_cmd="",
                 input_files=[],
                 output_files=[]):
        self.name = name
        self.database = db
        self.attributes = attributes
        self.FlagsMap= FlagsMap
        self.exe_cmd=[exe_cmd]
        self.input=None
        self.input_files = input_files
        self.__main_dir__ = os.getcwd()
        self.run_case_main_dir = "omari"
        self.run_case_sub_dir="case"
        
        self.objects_to_be_copied=[]
        self.current_case_dir = None
        
        self.new = True
        self.run_type = "read_only"
        
        self.output_files ={"omari.csv":["Time","Pu239"]}
        self.outputs={}
        self.__output__att()
        
    def import_database(self,filename="omari.xlsx",sheetname="omari"):
        self.database = pd.read_excel(filename,sheet_name=sheetname)
        self.attributes = list(self.database.columns)
        return self
    
    def __output__att(self):
        """
        this function for internal use only!
        it aims to parsing the self.out_files
        to be modified in the future.
        """
        for _,val in self.output_files.items():
            for att in val:
                self.outputs[att]=[]
        self.outputs_db=pd.DataFrame()
        return self
    
    def import_FlagsMap(self,
                        filename="omari.xlsx",
                        sheetname="omari"):
        """
        import flag map from excel file.
        
        Remark: Csv and json files will be supported in future
        
        """
        tmp = pd.read_excel(filename,sheet_name=sheetname)

        self.FlagsMap = {flag:att for flag,att in zip(
            tmp["flag"],tmp["attribute"])}
        return self
    
    def add_file(self,*file:File()):
        for f in file:
            if not isinstance(file,File):
                Warning("Bad entry",type(file),type(File))
                #return self
            if f not in self.input_files:
                self.input_files.append(f.read())
            else:
                print("duplicate file!")
        return self
    
    def launch_case(self,case_id:int=None,**kw):
        if case_id is not None:
            self.case_id=case_id

        i=self.case_id
        
        # -----------------------------------------------------------------
        # set/create current working directory 
        self.current_case_dir = os_cmd.set_fullpath(#os.path.join(
            self.__main_dir__, self.run_case_main_dir,
            f"{self.run_case_sub_dir}_{self.case_id}")
        #print(i,"flagsmap:",flagsmap)
        
        # -----------------------------------------------------------------
        # create case subdirectory 
        if self.new:
            # -------------------------------------------------------------
            # Make case subdirectory
            os_cmd.mkdir(self.current_case_dir)
            
            # -------------------------------------------------------------
            # copy objects (files/folders) to the case subdirecory
            for f in self.objects_to_be_copied:
                os_cmd.cp(f,self.current_case_dir)
           
            # --------------------------------------------------------------
            # get_data_from database
            rw ={att:val for att,val in self.database.iloc[i].items()}
            flagsmap = self.FlagsMap.get_flags_values(rw)
            
            # -------------------------------------------------------------
            # write input files in the case subdirecory
            self.__write_input__(flagsmap)
        
            #execute commands
            self.__execute__()
        
        # read output_files
        self.__read_outputs__()
        
        # execute post execution fucntions
        self.__execute_post_execution_functions__()

        return self
        
    def create_case_main_dir(self):
        return self.initialization()
    
    def initialization(self):
        cases_root_path= os_cmd.set_fullpath(self.__main_dir__, self.run_case_main_dir)
        if self.run_type!="new":
            self.new = False
        else:
            self.new = True
            os_cmd.rmdir(cases_root_path)
        os_cmd.mkdir(cases_root_path)
        return self
    
    def launch(self,**kw):
        """
        TO BE ADDED
        """
        self.initialization()
        self.__output__att()
        for i in progress_bar(name=self.name, start=0,end=len(self.database)):
            if self.__shall_stop():
                print("Luncher has been stoped by user")
                break
            # -----------------------------------------------------------------
            self.case_id=i    
            self.launch_case(**kw)
              
        return self
    
    def __shall_stop(self):
        return os_cmd.isfile(os_cmd.set_fullpath(self.__main_dir__,self.run_case_main_dir,"STOP_ALL"))    
    
    def __execute__(self):
        self.__cd__(self.current_case_dir)
        A=[]
        try: 
            A= [os.system(x) for x in self.exe_cmd]
        except:
            pass
        self.__cd__(self.__main_dir__)
        return A
        
        # if isinstance(self.exe_cmd, (tuple,list)):
        #     for cmd in self.exe_cmd:
        #         #print(cmd)
        #         p=subprocess.Popen([cmd],shell=True,cwd=self.current_case_dir,
        #                            )
        #         p.wait()
        #         while p.stdout.readable():
        #             line = p.stdout.readline()
                
        #             if not line:
        #                 break
                
        #             print(line.strip())
        #         #p.errors()
        # elif isinstance(self.exe_cmd, (str,)):
        #     p=subprocess.Popen([self.exe_cmd],shell=True,cwd=self.current_case_dir)
        #     p.wait()

        # return #os.system(self.exe_cmd)

    
    def __cd__(self,Dir):
        os.chdir(Dir)
        return self
    
    def __write_input__(self,flagsmap):
        for f in self.input_files:
            f.replace(flagsmap)
            #print(os.path.join(case_path, f.filename))
            f.write(os.path.join(self.current_case_dir, f.filename))
        return self
    
    def __read_outputs__(self):
        for fname,cols in self.output_files.items():
            fullname=os.path.join(self.current_case_dir, fname)
            df = pd.read_csv(fullname, usecols = cols, low_memory = True)
            pass
            for c in cols: 
                self.outputs[c].append(df[c])
                #self.outputs_db[c][self.case_id]=df[c]
        return self
        
    def __execute_post_execution_functions__(self):
        pass
        
    def __kwargs_hanlder(self,**kwd):
        for item,val in kwd.items():
            if item in self.__dict__:
                self.__setattr__(item, val)
            pass
                        
        


if __name__=="__main__":
    from matplotlib import pyplot as plt
  
    
    A=Case()
    df=pd.DataFrame(data=dict(RHO=np.random.uniform(18,20,500),
                              WF=np.random.uniform(0.005,0.050,500)))
    
    df.to_excel("omari.xlsx","data",engine="xlsxwriter")
    A.import_database(sheetname="data")
    F = Flags().add_flag(flag("#RHO@@#","RHO","%5.2f"),
                         flag("#@wf@#","WF","%10s"),
        
        )
    A.FlagsMap=F
    f = File(filename="./dummy_functions/input_file_2.py").read()
    A.add_file(f)
    #A.__main_dir__ = "/home/omari/Desktop/labeeb_test"
    A.exe_cmd =["python dummy_functions/input_file_2.py"]
    A.objects_to_be_copied=["README.md","test"]
    A.run_type = "new"
    A.run_case_main_dir="pu_simulator_sa"
    A.output_files={}
    A.launch()
    print(F.get_flags_values(dict(RHO=123)))
    

    # X=[]
    # df2=pd.DataFrame(A.outputs)
    # for i in range(len(A.database)):
    #     X.append([x for x in df2["Pu239"][i]][-1])
    
    # plt.plot(A.database.WF,np.array(X)*239/6.023e23*4907*180/1000,"X")
