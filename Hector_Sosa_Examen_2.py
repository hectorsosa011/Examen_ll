# -*- coding: utf-8 -*-
"""
Created on Thu Apr  8 10:34:21 2021

@author: hects
"""

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import os
import snappy
from snappy import Product
from snappy import ProductIO
from snappy import ProductUtils 
from snappy import WKTReader
from snappy import HashMap
from snappy import GPF
# Para leer shapefiles
import shapefile
import pygeoif



import tkinter as tk
#from tkinter import *
from tkinter import filedialog 


#path_to_sentinel_data = "C:/CTE_334/Actividad_09/data/S1B_IW_GRDH_1SDV_20201119T235742_20201119T235807_024341_02E47D_DCF6.zip"
#product = ProductIO.readProduct(path_to_sentinel_data)

#path_to_shapefile = "shape/villanueva.shp"

def infoproducto(product):
    #Leer y mostrar la informaciónd de la imagen
    width = product.getSceneRasterWidth()
    print("Width: {} px".format(width))
    height = product.getSceneRasterHeight()
    print("Height: {} px".format(height))
    name = product.getName()
    print("Name: {}".format(name))
    band_names = product.getBandNames()
    print("Band names: {}".format(", ".join(band_names)))
    
def plotBand(product, band, vmin, vmax):
    band = product.getBand(band)
    w = band.getRasterWidth()
    h = band.getRasterHeight()
    print(w, h)
    band_data = np.zeros(w * h, np.float32)
    band.readPixels(0, 0, w, h, band_data)
    band_data.shape = h, w
    width = 12
    height = 12
    plt.figure(figsize=(width, height))
    imgplot = plt.imshow(band_data, cmap=plt.cm.binary, vmin=vmin, vmax=vmax)
    return imgplot
      
def procesoShapefile(path_to_shapefile):
    r = shapefile.Reader(path_to_shapefile)
    g = []
    for s in r.shapes():
        g.append(pygeoif.geometry.as_shape(s))
        m = pygeoif.MultiPoint(g)
        global wkt
    return str(m.wkt).replace("MULTIPOINT", "POLYGON(") + ")"
        
#procesoShapefile(path_to_shapefile)
#wkt= procesoShapefile(path_to_shapefile)
    ##Aplicar correccion orbital
    
#path_to_sentinel_data = "C:/CTE_334/Actividad_09/data/S1B_IW_GRDH_1SDV_20201119T235742_20201119T235807_024341_02E47D_DCF6.zip"
#product = ProductIO.readProduct(path_to_sentinel_data)

def preproceso(product, wkt):
    global HashMap
    parameters = HashMap()
    GPF.getDefaultInstance().getOperatorSpiRegistry().loadOperatorSpis()
    parameters.put('orbitType', 'Sentinel Precise (Auto Download)')
    parameters.put('polyDegree', '3')
    parameters.put('continueOnFail', 'false')
    global apply_orbit_file
    apply_orbit_file = GPF.createProduct('Apply-Orbit-File', parameters, product)
   
    #Usar el shapefile para cortar la imagen
#def CorteUsandoShapefile(product, apply_orbit_file, wkt):
 #   global HashMap
    SubsetOp = snappy.jpy.get_type('org.esa.snap.core.gpf.common.SubsetOp')
    bounding_wkt = wkt
    geometry = WKTReader().read(bounding_wkt)
    HashMap = snappy.jpy.get_type('java.util.HashMap')
    GPF.getDefaultInstance().getOperatorSpiRegistry().loadOperatorSpis()
    parameters = HashMap()
    parameters.put('copyMetadata', True)
    parameters.put('geoRegion', geometry)
    product_subset = snappy.GPF.createProduct('Subset', parameters, apply_orbit_file)


    #Mostrar las dimensiones de la imagen
    width = product_subset.getSceneRasterWidth()
    print("Width: {} px".format(width))
    height = product_subset.getSceneRasterHeight()
    print("Height: {} px".format(height))
    band_names = product_subset.getBandNames()
    print("Band names: {}".format(", ".join(band_names)))
    band = product_subset.getBand(band_names[0])
    print(band.getRasterSize())
    plotBand(product_subset, "Intensity_VV", 0, 100000)
    #return product_subset

#def CalibracionImagen(product_subset):
        ##Aplicar la calibracion de la imagen
    parameters = HashMap()
    parameters.put('outputSigmaBand', True)
    parameters.put('sourceBands', 'Intensity_VV')
    parameters.put('selectedPolarisations', "VV")
    parameters.put('outputImageScaleInDb', False)
    product_calibrated = GPF.createProduct("Calibration", parameters, product_subset)
    plotBand(product_calibrated, "Sigma0_VV", 0, 1)

#def filtroSpeckle(product_calibrated):      
    ##Aplicar el filtro Speckle
    filterSizeY = '5'
    filterSizeX = '5'
    parameters = HashMap()
    parameters.put('sourceBands', 'Sigma0_VV')
    parameters.put('filter', 'Lee')
    parameters.put('filterSizeX', filterSizeX)
    parameters.put('filterSizeY', filterSizeY)
    parameters.put('dampingFactor', '2')
    parameters.put('estimateENL', 'true')
    parameters.put('enl', '1.0')
    parameters.put('numLooksStr', '1')
    parameters.put('targetWindowSizeStr', '3x3')
    parameters.put('sigmaStr', '0.9')
    parameters.put('anSize', '50')
    speckle_filter = snappy.GPF.createProduct('Speckle-Filter', parameters, product_calibrated)
    plotBand(speckle_filter, 'Sigma0_VV', 0, 1)

#def CorreccionTerreno(speckle_filter):
    ##Aplicar la correccion del terremo
    parameters = HashMap()
    parameters.put('demName', 'SRTM 3Sec')
    parameters.put('pixelSpacingInMeter', 10.0)
    parameters.put('sourceBands', 'Sigma0_VV')
    global speckle_filter_tc
    speckle_filter_tc = GPF.createProduct("Terrain-Correction", parameters, speckle_filter)
    plotBand(speckle_filter_tc, 'Sigma0_VV', 0, 0.1)
#        return(speckle_filter_tc)
    
#preproceso(product)

#prueba     
def MascaraBinariaInundacion(speckle_filter_tc):
    #Crear una mascara binaria para la inundacion
    parameters = HashMap()
    BandDescriptor = snappy.jpy.get_type('org.esa.snap.core.gpf.common.BandMathsOp$BandDescriptor')
    targetBand = BandDescriptor()
    targetBand.name = 'Sigma0_VV_Flooded'
    targetBand.type = 'uint8'
    targetBand.expression = '(Sigma0_VV < 1.57E-2) ? 1 : 0'
    targetBands = snappy.jpy.array('org.esa.snap.core.gpf.common.BandMathsOp$BandDescriptor', 1)
    targetBands[0] = targetBand
    parameters.put('targetBands', targetBands)
#    global flood_mask
    flood_mask = GPF.createProduct('BandMaths', parameters, speckle_filter_tc)
    plotBand(flood_mask, 'Sigma0_VV_Flooded', 0, 1)
    
#MascaraBinariaInundacion(speckle_filter_tc)       
    
def CrearImagenMascara(flood_mask):
    #    #Crear la imagen a partir de la mascara
    ProductIO.writeProduct(flood_mask, "data/final_mask", 'GeoTIFF')
    os.path.exists("data/final_mask.tif")



import tkinter as tk
#from tkinter import *
from tkinter import filedialog 

##crear la ventana
ventana = tk.Tk()
ventana.geometry("1024x720")
#decoraciontamaño ventana
ventana['bg'] = 'azure'
ventana.title("Inundacion")

#####################################################################
folder_path = tk.StringVar()
def BuscarDir_botton():
    filedir = filedialog.askopenfile(title="Abrir Archivo", initialdir="C:/", filetypes=(("Archivos Zip","*.zip"), ("Todos los Archivos","*.*")))
    file_name = filedir.name
    folder_path.set(file_name)
 
label = tk.Label(ventana, text= '1. Seleccionar la imagen satelitar a utilizar')
label.pack()

botonDir = tk.Button(text = 'Seleccionar imagen', command = BuscarDir_botton)
botonDir.pack()

textDir = tk.Entry(ventana, textvariable=folder_path, width=70)
textDir.pack()

##################################################################### 
folder_path2 = tk.StringVar()
def BuscarFile_botton():
    filedir2 = filedialog.askopenfile(title="Abrir Archivo", filetypes=(("Archivos Shp","*.shp"), ("Todos los Archivos","*.*")))
    file_name2 = filedir2.name
    folder_path2.set(file_name2)

label2 = tk.Label(ventana, text= '2. Seleccionar el Shapefile de la zona a analizar')
label2.pack()

bottonDir2 = tk.Button(text = 'Seleccionar Shapefile', command = BuscarFile_botton)
bottonDir2.pack()

textDir2 = tk.Entry(ventana, textvariable=folder_path2, width=70)
textDir2.pack()

##################################################################### 
def proceso():
    texto = textDir.get()
    texto2 = textDir2.get()
    
    path_to_sentinel_data = "{}".format(texto)  
    print(path_to_sentinel_data)
    
    product = ProductIO.readProduct(path_to_sentinel_data)
    
    infoproducto(product)
    
    path_to_shapefile = "{}".format(texto2)
    wkt = procesoShapefile(path_to_shapefile)
    
    
    preproceso(product, wkt)

label3 = tk.Label(ventana, text= '3. Comenzar a pre procesar la imagen')
label3.pack()

boton3 = tk.Button(ventana, text = "Preprocesar imagen", command = proceso)
boton3.pack() 

##################################################################### 

def MascaraBinariaInundacion1():
    texto3 = cajatexto.get()
    print(texto3)    
    parameters = HashMap()
    BandDescriptor = snappy.jpy.get_type('org.esa.snap.core.gpf.common.BandMathsOp$BandDescriptor')
    targetBand = BandDescriptor()
    targetBand.name = 'Sigma0_VV_Flooded'
    targetBand.type = 'uint8'
    targetBand.expression = '(Sigma0_VV < {}E-2) ? 1 : 0'.format(texto3)   
    targetBands = snappy.jpy.array('org.esa.snap.core.gpf.common.BandMathsOp$BandDescriptor', 1)
    targetBands[0] = targetBand
    parameters.put('targetBands', targetBands)
    global flood_mask
    flood_mask = GPF.createProduct('BandMaths', parameters, speckle_filter_tc)
    plotBand(flood_mask, 'Sigma0_VV_Flooded', 0, 1)

label4 = tk.Label(ventana, text= '4. Definir el Umbrar para la máscara de agua')
label4.pack()

cajatexto = tk.Entry(ventana, width=70)
cajatexto.pack()   

boton4 = tk.Button(ventana, text = "Aplicar la máscara", command = MascaraBinariaInundacion1)
boton4.pack() 

##################################################################### 

def crear():
    
    CrearImagenMascara(flood_mask)


botton5 = tk.Button(ventana, text= "Crear el archivo", command=crear)
botton5.pack()

###################### Intento de mostrar la imgagen ##########################
##################################################################### 
#from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, 
#NavigationToolbar2Tk)
#from matplotlib.figure import Figure
#def mostrar():
#    fig = Figure(figsize = (5, 5), dpi = 100)
    
#    canvas = FigureCanvasTkAgg(fig, master = ventana)
#    canvas.get_tk_widget().pack()
#    canvas.draw()


##################################################################### 
##################################################################### 

ventana.mainloop()
