import os, shutil


'''
    Objet qui permet de créer une structure de dossier pour stocker des résultats de traitement (temporaire et permanant).
    La structure de dossier permet de conserver les intrants, les résultats intermédiaires et les résultats finaux.
    
    Ex de la strucutre:
        - Working_dir (existant)
            - dossier_temp (créer)
                - Fichier temporaire
            - Fichier résulats finaux
'''
class workingEnv():
    
    def __init__ (self, working_dir):
        # Vérifier si l'environement de travail est valide
        if os.path.exists(working_dir): self.working_dir = working_dir
        else: raise ValueError("Le dossier {} n'existe pas'".format(working_dir))
        
        self.dossier_travail = None
        self.dossier_temp = None

    def createDirectories(self, name):
        # Dossier unique au bassin versant
        self.dossier_travail = self.working_dir + name
        # Dossier Temporaire du bassin versant
        self.dossier_temp = self.dossier_travail + '\Temporaire'
        
        # Pour chaque dossier, créer le dossier si inexistant
        for dos in [self.dossier_travail, self.dossier_temp]:
            # Créer le dossier si inexistant
            if not os.path.exists(dos): os.makedirs(dos)
        
        return True
    
    def getWorkingDir(self):
        return self.working_dir
    
    def getResultDir(self):
        return self.dossier_travail
    
    def getTempDir(self):
        return self.dossier_temp

    def getWorkingFile(self, file_name, file_extention=''):
        if file_extention: return self.working_dir + file_name + file_extention
        else: return self.working_dir + file_name


    def deleteTemporaryDir(self):
        """ param <path> could either be relative or absolute. """
        if os.path.isfile(self.dossier_temp) or os.path.islink(self.dossier_temp):
            os.remove(self.dossier_temp)  # remove the file
        elif os.path.isdir(self.dossier_temp):
            shutil.rmtree(self.dossier_temp)  # remove dir and all contains
        else:
            raise ValueError("file {} is not a file or dir.".format(self.dossier_temp))
            
        self.dossier_temp = None
    
    def createGlobalFile(self, file_name):
        global_file = None
        if self.working_dir:
            global_file = self.working_dir + file_name
        
        return global_file
    
    def createTemporaryFile(self, file_name):
        temp_file = None
        if self.dossier_temp:
            temp_file = self.dossier_temp + '\\' + file_name
        
        return temp_file
    
    def createResultFile(self, file_name):
        res_file = None
        if self.dossier_travail:
            res_file = self.dossier_travail + '\\' + file_name
        
        return res_file