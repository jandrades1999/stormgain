import logging
import json
import os
import time
from typing import final

from PIL import Image
from selenium import webdriver
from selenium.common.exceptions import ElementNotInteractableException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

BASEDIR = os.getcwd()
BASEDIR = "D:/proyectos/stormgain"

with open(BASEDIR + '/credentials.json') as json_file:
    file = json.load(json_file)
    username = file['user']
    password = file['password']



class Stormgain():
    def __init__(self):
        self.geckodriver_path = 'D:/proyectos/stormgain/geckodriver.exe'
        self.stormgain_url = 'http://www.stormgain.com/es-es'

    def get_snap(self, driver):
        driver.save_screenshot('snap.png')
        snap_obj = Image.open('snap.png')
        return snap_obj
    
    def get_image(self, driver):
        # Obtenemos la imagen completa
        img_elementg = driver.find_element_by_xpath('//div[@class="geetest_panel_next"]//canvas[@class="geetest_canvas_bg geetest_absolute"]')

        #obtenemos el tamaño de la imagen para ajustar el cuadro deslizante
        size = img_elementg.size

        left = img_elementg.location['x']
        top = img_elementg.location['y']
        right = left+size['width']
        bottom = top+size['height']
        
        snap_obj = self.get_snap(driver) # Obtenemos el fragmnento separado
        img_obj = snap_obj.crop((left, top, right, bottom))# Generamos una nueva imagen con el tamaño del cuadro a replicar

        return img_obj
    
    def get_distance(self, img1,img2):
        start_x=60# the original x 
        threhold=60# the threshold value 
        for x in range(start_x,img1.size[0]):
            for y in range(img1.size[1]):
                rgb1=img1.load()[x,y]
                rgb2=img2.load()[x,y]
                res1=abs(rgb1[0]-rgb2[0])
                res2=abs(rgb1[1]-rgb2[1])
                res3=abs(rgb1[2]-rgb2[2])
                if not (res1<threhold and res2<threhold and res3<threhold):
                    return x-7# after the test -7 you can increase your success rate 

    def get_tracks(self, distance):
        #Distancia total obtenida en el paso anterior. 20 ites un pixel que volverá atrás despues. 
        distance+=20
        """
            v0 --> Velocidad inicial
            s  --> distancia viajada
            t  --> Tiempo
            mid--> Distancia que reducir
        """
        v0=2
        s=0
        t=0.4
        mid=distance*3/5
        # Guardar las distancias
        forward_tracks=[]
        while s<distance:
            if s<mid:
                a=2
            else:
                a=-3
            # high school physics, uniform acceleration distance calculation 
            v=v0
            tance=v*t+0.5*a*(t**2)
            tance=round(tance)
            s+=tance
            v0=v+a*t
            forward_tracks.append(tance)
        # because back 20 pixels ， so you can manually type as long as and for 20 can be 
        back_tracks = [-1, -1, -1, -2, -2, -2, -3, -3, -1]  # 20
        return {"forward_tracks": forward_tracks, 'back_tracks': back_tracks}

    def bypass_slize(self, driver):
        try:
            none_img = self.get_image(driver)
            driver.execute_script("var x=document.getElementsByClassName('geetest_canvas_fullbg geetest_fade geetest_absolute')[0];"
                    "x.style.display='block';"
                    "x.style.opacity=1"
                    )
            block_img = self.get_image(driver)

            slider_button = driver.find_element_by_class_name('geetest_slider_button')
            distance = self.get_distance(block_img, none_img)
            tracks_dict = self.get_tracks(distance)
            forword_tracks = tracks_dict['forward_tracks']
            back_tracks = tracks_dict['back_tracks'][:-2]
            ActionChains(driver).click_and_hold(slider_button).perform()
            ## TODO: Terminar bloque 

            ##% Sumamos los movimientos para incrementar la velocidad 
            index_to_be_deleted = []
            for i in range(0, len(forword_tracks), 2):
                forword_tracks[i] = forword_tracks[i] + forword_tracks[i+1]
                index_to_be_deleted[i] = i + 1
            
            ###################################################################
            for forward_track in forword_tracks:
                ActionChains(driver).move_by_offset(xoffset=forward_track, yoffset=0).perform()
                logging.info(forward_track)
            for back_tracks in back_tracks:
                ActionChains(driver).move_by_offset(xoffset=back_tracks, yoffset=0).perform()
                print(back_tracks)

            ActionChains(driver).move_by_offset(xoffset=0, yoffset=0).perform()
            ActionChains(driver).move_by_offset(xoffset=0, yoffset=0).perform()
            ActionChains(driver).release().perform()

            time.sleep(2)

            return True
        except Exception as e:
            logging.error(e)
            return False


    def log_in(self):
        try:
            driver = webdriver.Firefox(executable_path=self.geckodriver_path)
            driver.get(self.stormgain_url)
            time.sleep(3)

            log_in_button = driver.find_element_by_class_name("sign_in_link sm-hidden btn menu-item__link".replace(" ", "."))

            log_in_button.click()
            time.sleep(3)
            #Cerramos la pestaña anterior 
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            time.sleep(2)

            driver.find_element_by_name("login").send_keys(username)
            driver.find_element_by_name("password").send_keys(password)
            driver.find_element_by_xpath('//div[@class="controls"]//input[@class="btn btn-mint btn-login"]').click()
            time.sleep(3)

            logged = False
            retry = 0
            while not logged:
                try:
                    logged = self.bypass_slize(driver)
                except Exception as e:
                    logging.error(e)
                    retry += 1
                    if retry >= 5:
                        raise Exception("Error al iniciar sesión")

            time.sleep(3)
            driver.find_element_by_xpath('//a[@href="' + '/crypto-miner/' + '"]').click()
            
            try:
                self.bypass_slize(driver)
            except Exception as e:
                logging.error(e)
                pass

        finally:
            driver.quit()





    def run(self):
        
        try:
            log_in = self.log_in()
        except Exception as e:
            logging.error(e)

if __name__ == '__main__':
    stormgain = Stormgain()
    stormgain.run()
