# -*- coding: utf-8 -*-
from qgis.core import QgsPointXY, QgsGeometry, QgsVectorLayer, QgsField, QgsProject, QgsFeature
from qgis.PyQt.QtCore import QVariant
import pyodbc
import pandas as pd

class PanneauGSR:
    """ Objet qui permet de ce connecter à la Base de données GSR et de retourner des panneaux """
    def __init__(self, dt='90', dsn='GSR'):
        self.dt = dt
        self.setConnectionString(dsn)
        # Liste des champs à conserver
        self.list_fields = ("NO_INSTL", "GEO_LONGT", "GEO_LATTD",
                        "NOM_RTSS", "VAL_CHANG", "Message",
                        "NSR_PHOTO_trim", "DES_ORDRE", 
                        "DES_EMPLC", "NOM_DT", "IND_VIRTUEL")

        # Requête de connection a la BD GSR
        self.sql = "select %s from GSR_V_PANNX" % ', '.join(self.list_fields)

    def testConnection(self, conextion_str=''):
        try:
            # Connection ODBC
            with pyodbc.connect(self.connextion_str) as conn: return True
        except: return False
    
    def setConnectionString(self, dsn):
        self.connextion_str = 'DSN=%s' % dsn
        self.dsn_is_valide = self.testConnection(self.connextion_str)
    
    def getPanneau(self, code_nsr, add_layer=True):
        """
        Méthode qui permet d'ajouter une couche temporaire dans la carte qui contient 
        la localisation des panneaux selon le code NSR.

        Args:
            - code_nsr (Liste of str): Liste des codes NSR des panneaux ex: ["I-185-1", "I-185-2"]
            - add_layer (bool): Ajouter la couche résultat au projet
        """
        if self.dsn_is_valide:
            # Lire la table des panneaux dans un data frame Pandas
            with pyodbc.connect(self.connextion_str) as conn: data = pd.read_sql(self.sql, conn)

            # Conversion des types utilisé pour limiter l'espace
            data["NOM_DT"] = data["NOM_DT"].astype("category")
            data["NSR_PHOTO_trim"] = data["NSR_PHOTO_trim"].astype("category")
            data["NOM_RTSS"] = data["NOM_RTSS"].astype("category")
            data[["GEO_LONGT", "GEO_LATTD"]] = data[["GEO_LONGT", "GEO_LATTD"]].apply(pd.to_numeric, downcast="float")
            # Mettre le champs messages en Text si NULL
            data["Message"].fillna("")
            # Mettre le champs messages toute en minuscule
            data['Message'] = data['Message'].str.lower()

            # Produire la requete à utiliser en fonction des Code NSR 
            request = '(%s)' % (' or '.join(['NSR_PHOTO_trim == "%s"' % code for code in code_nsr]))
            request += ' and NOM_DT == "%s"' % "DG de l'Estrie"

            # Appliquer la requete sur le DataFrame
            panneaux_filtre = data.query(request)
                        
            # Créer une couche ponctuelle pour les panneaux
            vl = QgsVectorLayer("Point?crs=EPSG:4326", 'Panneaux', "memory")
            # Ajouter les champs du DataFrame
            fields = [QgsField(head, QVariant.String) for head in panneaux_filtre]
            pr = vl.dataProvider()
            pr.addAttributes(fields)
            vl.updateFields()
            fields = vl.fields()

            feats = []
            # Parcourir les panneaux qui réponds à la requête NSR et Message
            for i, panneau in panneaux_filtre.iterrows():
                ordre_panneau = panneau["DES_ORDRE"]
                # Liste des attributs de l'entité panneau
                att = list(panneau.array)
                # Créer une nouvelle entité
                feat = QgsFeature(fields)
                # Set la géometry ponctuelle avec les coordonnée Long/Lat
                feat.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(panneau['GEO_LONGT'], panneau['GEO_LATTD'])))
                # Set les attributs
                feat.setAttributes(att)
                feats.append(feat)

            # Ajouter les entitées à la couche
            pr.addFeatures(feats)
            vl.updateExtents()
            # Ajouter la couche au projet
            if add_layer: QgsProject.instance().addMapLayer(vl)
            return vl
    
    
    ''' *** À titre informatique seulement, ne fonctionne pas *** '''
    def getPanneauEtSousPanneau(self):
        # Conversion des types utilisé pour limiter l'espace
        data["NOM_DT"] = data["NOM_DT"].astype("category")
        data["NSR_PHOTO_trim"] = data["NSR_PHOTO_trim"].astype("category")
        data["NOM_RTSS"] = data["NOM_RTSS"].astype("category")
        data[["GEO_LONGT", "GEO_LATTD"]] = data[["GEO_LONGT", "GEO_LATTD"]].apply(pd.to_numeric, downcast="float")
        # Mettre le champs messages en Text si NULL
        data["Message"].fillna("")
        # Mettre le champs messages toute en minuscule
        data['Message'] = data['Message'].str.lower()

        installation = data.groupby('NO_INSTL')

        # Text à contenir pour le filtre du champ message  
        filtre_message = 'vins'
        # Liste des codes NSR à conserver 
        code_nsr = ["I-185-1", "I-185-2", "I-185-3"]
        # Produire la requete à utiliser en fonction des Code NSR 
        request = '(%s)' % (' or '.join(['NSR_PHOTO_trim == "%s"' % code for code in code_nsr]))
        # Ajouter à la requete la condition du champ Message
        #request += ' and Message.str.contains("%s")' % filtre_message
        request += ' and NOM_DT == "%s")' % "DG de l'Estrie"

        # Appliquer la requete sur le DataFrame
        panneaux_filtre = data.query(request)
                    
        # Créer une couche ponctuelle pour les panneaux
        vl = QgsVectorLayer("Point?crs=EPSG:4326", 'Panneaux', "memory")
        # Ajouter les champs du DataFrame
        fields = [QgsField(head, QVariant.String) for head in panneaux_filtre]
        # Ajouter un champ sous panneaux pour la combinaisaon des panneaux
        fields.append(QgsField('sous_panneaux', QVariant.String))
        fields.append(QgsField('Etiquette', QVariant.String))
        pr = vl.dataProvider()
        pr.addAttributes(fields)
        vl.updateFields()
        fields = vl.fields()

        feats = []
        # Parcourir les panneaux qui réponds à la requête NSR et Message
        for i, panneau in panneaux_filtre.iterrows():
            ordre_panneau = panneau["DES_ORDRE"]
            # Recupérer tout les panneaux sur l'installation du panneau
            panneaux_sur_installation = installation.get_group(panneau['NO_INSTL'])
            # Valeur par défault du champ sous panneaux
            nsr_sous_panneau = ''
            # Parcourir les panneaux de l'installation'
            for row, sous_panneau in panneaux_sur_installation.iterrows():
                # Définir la premiere partie du code NSR
                code = sous_panneau['NSR_PHOTO_trim'][:6]
                # Vérifier si le codes du panneau est utiliser pour Info et circuit touristique
                if code == 'I-240-' or code == 'I-230-':
                    # Vérifier selon l'ordre si le panneaux est directement en dessous
                    if sous_panneau["DES_ORDRE"] == (int(ordre_panneau) -10):
                        # Définir le code du sous panneau
                        nsr_sous_panneau = sous_panneau['NSR_PHOTO_trim']
                        # Seulement 1 sous panneau possible
                        break
                    
            # Liste des attributs de l'entité panneau
            att = list(panneau.array)
            # Ajouter le sous panneaux
            att.append(nsr_sous_panneau)
            # Ajouter l'étiquette
            etiquette = ''
            if panneau['NSR_PHOTO_trim'] in dict_ref_etiquette:
                if nsr_sous_panneau in dict_ref_etiquette[panneau['NSR_PHOTO_trim']]:
                    etiquette = str(dict_ref_etiquette[panneau['NSR_PHOTO_trim']][nsr_sous_panneau])
                    
            att.append(etiquette)
            
            # Créer une nouvelle entité
            feat = QgsFeature(fields)
            # Set la géometry ponctuelle avec les coordonnée Long/Lat
            feat.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(panneau['GEO_LONGT'], panneau['GEO_LATTD'])))
            # Set les attributs
            feat.setAttributes(att)
            feats.append(feat)

        # Ajouter les entitées à la couche
        pr.addFeatures(feats)
        vl.updateExtents()
        # Ajouter la couche au projet
        QgsProject.instance().addMapLayer(vl)



