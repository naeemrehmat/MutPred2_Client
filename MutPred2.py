import re
import requests
import mechanize
import pickle
import os

class Job():
    def __init__(self , email, fasta_sequence , p_value=0.5 ):
        self.email=email
        self.fasta_sequence = fasta_sequence
        self.p_value = str(p_value)
        self.job_id=None
        self.job_status=None
        self.result = None

    def submit_job( self ):
        
        try:
            br = mechanize.Browser()
            br.open("http://mutpred2.mutdb.org/#qform")
            br.select_form(nr=0)
            br.form['email'] = self.email
            br.form['data']  = self.fasta_sequence
            br.form['pval']  = self.p_value
            req = br.submit()
            res_data = req.get_data()
            if str(res_data).find("Your job has been successfully submitted with an ID")!=-1 :
                self.job_id = re.findall("[a-z0-9]{8}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{12}" , str(res_data)  )[0]
                print(  "Job Submitted Successfully and Job ID:" , self.job_id  )

            else:
                print("Error Occured\n" , res_data )
                
        except Exception as exp:
            print( exp )
        
        return
        
    def check_job_status( self ):
        if self.job_status=="DONE":
            return self.job_status

        job_response=None
        try:
            job_response=requests.post("http://mutpred2.mutdb.org/cgi-bin/mutpred2_output.py?jobid="+self.job_id,verify=False)
            if  job_response.text.find("Internal Server Error")!=-1:
                self.job_status="RUNNING"
            elif job_response.text.find("Your predictions may not be completed yet")!=-1:
                self.job_status="RUNNING"
            elif job_response.text.find("Download results")!=-1:
                self.job_status="DONE"
            else:
                print( "Incorrect Job ID" )

        except Exception as exp:
            print( exp , job_response )    

        return self.job_status
    
    def job_result(self):
        if self.check_job_status()=="DONE":
            if self.result!=None:
                return self.result
            
            try:
                self.result = requests.post( "http://mutpred2.mutdb.org/tmp/"+self.job_id+".csv", verify=False ).text
            except Exception as exp:
                print("Could Not Fetch Results:", exp )
        else:
            print( "Please Wait Job is not completed yet" )

        return self.result
    
    
        
class MutPred2_Client():
    
    def __init__(self ):
        
        self.jobs = []
        
        if os.path.isfile("recover_client.pkl") :
            print("We have detected a recovery point; do you want to recover previous jobs?")
            option = input( "Enter 1 to recover OR, 0 to ignore = " )
            
            if option=="1" :
                with open("recover_client.pkl","rb") as f:
                    self =  pickle.load( f )
                
            """
            self.email= temp_client.email
            self.fasta_sequence = temp_client.fasta_sequence
            self.p_value = temp_client.p_value
            self.job_id= temp_client.job_id
            self.job_status= temp_client.job_status
            self.result =  temp_client.result
            """
       
            
            
    
    
        
    def add_job( self , email ,fasta_sequence , p_value=0.5  ):
        for job_ in self.jobs:
            if job_.fasta_sequence==fasta_sequence:
                print( "Job is already running and job ID:" , job_.job_id )
                return
        
        current_job = Job(email,fasta_sequence,p_value)
        current_job.submit_job()
        self.jobs.append( current_job )
        
        with open("recover_client.pkl","wb") as f:
            pickle.dump( self , f ) 
            
        return 
        
    def all_jobs_status(self):
        completed_jobs = 0
        running_jobs   = 0
        
        for job_ in self.jobs:
            if job_.check_job_status() =="DONE":
                completed_jobs += 1
            elif job_.check_job_status() =="RUNNING":
                running_jobs   += 1
            
                
        print(  "Completed Jobs =" , completed_jobs  )
        print(  "Running Jobs =" , running_jobs  )
        
    
    
    def save_results(self , file_name):
        data= "Gene_Name,Substitution,MutPred2_Score,Molecular_Mechanisms,Affected PROSITE and ELM Motifs,Remarks\n"
        jobs_completed = 0
        for job_ in self.jobs:
            if job_.job_result()!=None:
                data+= job_.job_result()
                jobs_completed += 1
        if jobs_completed >0:
            with open(file_name,"w") as f:
                f.write(data)
            print("Result of ",jobs_completed," completed jobs is saved in current directory as:" ,file_name )
        else:
            print("No Job is completed yet to be saved")
               
    
    

    
    
    
    
    
    
    
    