#!/usr/bin/env python
#
# Este tutorial demonstra o uso de tarefas. Uma tarefa é uma função que
# é chamado uma vez a cada frame. Eles são bons para coisas que precisam ser
# atualizado com muita frequência. No caso de asteróides, usamos tarefas para atualizar
# as posições de todos os objetos, e verificar se as balas ou os
# navio atingiu os asteróides
#

import os

from direct.showbase.ShowBase import ShowBase
from panda3d.core import TextNode, TransparencyAttrib
from panda3d.core import LPoint3, LVector3
from panda3d.core import SamplerState
from panda3d.core import ClockObject
from direct.gui.OnscreenText import OnscreenText
from direct.gui.OnscreenImage import OnscreenImage
from direct.task.Task import Task
from math import sin, cos, pi
from random import randint, choice, random
from direct.interval.SoundInterval import SoundInterval
from direct.interval.MetaInterval import Sequence
from direct.interval.IntervalGlobal import *
from direct.interval.FunctionInterval import Wait, Func
from direct.gui.DirectGui import *
import time
import sys

# Constantes que irão controlar o comportamento do jogo
SPRITE_POS = 55     # No campo de visão padrão e uma profundidade de 55
textfim1 = 'a'      # Textos para aparecer na tela na derrota e na vitória
textfim2 = 'a'
textpontemp = 'a'
ini = 0             #constante para a pontuação
relo = 0            #constante para atualizar o tempo
SCREEN_X = 20       # Tela vai de -20 a 20 no X
SCREEN_Y = 15       # A tela vai de -15 a 15 em Y
TURN_RATE = 360     # Graus que o navio pode virar em 1 segundo
ACCELERATION = 10   # Aceleração do navio em unidades/seg
MAX_VEL = 6         # Velocidade máxima do navio em unidades/seg
MAX_VEL_SQ = MAX_VEL ** 2  # Quadrado da velocidade do navio
DEG_TO_RAD = pi / 180  # traduz graus para radianos para sin e cos
BULLET_LIFE = 1.5     # Quanto tempo as balas permanecem na tela antes de serem removidas
BULLET_REPEAT = .2  # Quantas vezes as balas podem ser disparadas
BULLET_SPEED = 10   # Velocidade das balas se movem
AST_INIT_VEL = 1    # Velocidade dos maiores asteróides
AST_INIT_SCALE = 3  # Escala inicial de asteroides
AST_VEL_SCALE = 2.2  # Quanta velocidade do asteroide se multiplica quando quebrada
AST_SIZE_SCALE = .6  # Quanta escala de asteroides muda quando quebrada
AST_MIN_SCALE = 1.4  # Se um asteroide for menor que isso e for atingido,desaparece em vez de se dividir

# Isso ajuda a reduzir a quantidade de código usada para carregar objetos, já que todos
# os objetos são praticamente os mesmos.

def loadObject(tex=None, pos=LPoint3(0, 0), depth=SPRITE_POS, scale=3, transparency=True):
    # Todos objeto usa o modelo plano e é parente da câmera
    # para que fique de frente para a tela.
    obj = loader.loadModel("models/plane")
    obj.reparentTo(camera)

    # Defina a posição inicial e a escala.
    obj.setPos(pos.getX(), depth, pos.getY())
    obj.setScale(scale)

    # Isso diz ao Panda para não se preocupar com a ordem em que as coisas são desenhadas
    # (ou seja, desabilitar o teste Z). Isso evita um efeito conhecido como Z-fighting
    obj.setBin("unsorted", 0)
    obj.setDepthTest(False)

    if transparency:
        # Ative a transparência
        obj.setTransparency(TransparencyAttrib.MAlpha)

    if tex:
        # Carregue e defina a textura solicitada.
        tex = loader.loadTexture("textures/" + tex)
        tex.setWrapU(SamplerState.WM_clamp)
        tex.setWrapV(SamplerState.WM_clamp)
        obj.setTexture(tex, 1)

    return obj
# Função semelhante a macro usada para reduzir a quantidade de código necessária para criar o
# instruções na tela
def genLabelText(text, i):
    return OnscreenText(text=text, parent=base.a2dTopLeft, pos=(0.07, -.06 * i - 0.1),
                        fg=(1, 1, 1, 1), align=TextNode.ALeft, shadow=(0, 0, 0, 0.5), scale=.05)

# Funções feitas para mostrar o tempo e a pontuação no topo da tela
cronometro = OnscreenText(text= "Tempo = "+str(relo), pos=(0.90, +0.80),
                        fg=(1, 1, 1, 1), shadow=(0, 0, 0, 0), scale=0.1 ,mayChange=1)

pontconfig = OnscreenText(text = "Pontuação = "+str(ini), pos = (0.90, + 0.90),
        scale = 0.1,fg=(1,1,1,1), shadow=(0, 0, 0, 0), mayChange=1)

textfim1 = OnscreenText(text='', pos=(0, 0.4),
                        fg=(1, 1, 1, 1), shadow=(0, 0, 0, 0.5), scale=0.15)

textfim2 = OnscreenText(text='', pos=(0, 0.2),
                        fg=(1, 1, 1, 1), shadow=(0, 0, 0, 0.5), scale=0.15)

textpontemp = OnscreenText(text='',
                           pos=(0, 0), fg=(1, 1, 1, 1), shadow=(0, 0, 0, 0.5), scale=0.15)

imagefim = OnscreenImage(image='image/vasof.png', pos=(0, 0, 0), scale=0)

valor = int(time.time()) #definir o valor do tempo

def novapont(arg): #Funções feitas para atualizar a pontuação e tempo
    text = "Pontuação = " +str(ini)
    pontconfig.setText(text)

def novorelo(arg):
    text = "Tempo = " +str(relo)
    cronometro.setText(text)

class AsteroidsIP(ShowBase):


    def __init__(self):
        # Inicializa a classe ShowBase da qual herdamos, que irá
        # cria uma janela e configura tudo que precisamos para renderizar nela.
        ShowBase.__init__(self)

        self.escapeText = genLabelText("ESC: Sair", 0)
        self.leftkeyText = genLabelText("[Seta Esquerda]: Virar p/ Esquerda", 1)
        self.rightkeyText = genLabelText("[Seta Direita]: Virar p/ Direita", 2)
        self.upkeyText = genLabelText("[Seta p/ cima]: Acelerar", 3)
        self.spacekeyText = genLabelText("[Espaço]: Atirar", 4)
        self.contkeyText = genLabelText("[O]: Reiniciar jogo", 5)

        # Desabilite o controle de câmera padrão baseado em mouse. Este é um método de
        # Classe ShowBase da qual herdamos.

        self.disableMouse()

        # Carregue a imagem de fundo.
        self.setBackgroundColor((0, 0, 0, 1))
        self.bg = loadObject("ImagemFundo.jpg", scale=160, depth=200,
                             transparency=False)

        # Carregue a aereonave e defina sua velocidade inicial.
        self.ship = loadObject("ship.png")
        self.setVelocity(self.ship, LVector3.zero())

        # Um dicionário de quais teclas estão sendo pressionadas no momento
        # Os eventos chave atualizam esta lista, e nossa tarefa irá consultá-la como entrada
        self.keys = {"turnLeft": 0, "turnRight": 0,
                     "accel": 0, "fire": 0}

        self.accept("escape", sys.exit)  # Saída de fuga
        # Outros eventos de chaves definem o valor apropriado em nosso dicionário de chaves
        self.accept("arrow_left",     self.setKey, ["turnLeft", 1])
        self.accept("arrow_left-up",  self.setKey, ["turnLeft", 0])
        self.accept("arrow_right",    self.setKey, ["turnRight", 1])
        self.accept("arrow_right-up", self.setKey, ["turnRight", 0])
        self.accept("arrow_up",       self.setKey, ["accel", 1])
        self.accept("arrow_up-up",    self.setKey, ["accel", 0])
        self.accept("space",          self.setKey, ["fire", 1])
        self.accept("o",              self.reiniciajogo)

        # Agora criamos a tarefa. taskMgr é o gerenciador de tarefas que realmente
        # chama a função a cada quadro. O método add cria uma nova tarefa.
        # O primeiro argumento é a função a ser chamada e o segundo
        # argumento é o nome da tarefa. Ele retorna um objeto de tarefa que
        # é passado para a função a cada quadro.
        self.gameTask = taskMgr.add(self.gameLoop, "gameLoop")

        # Armazena a hora em que a próxima bala pode ser disparada.
        self.nextBullet = 0.0

        # Esta lista armazenará balas disparadas.
        self.bullets = []

        # Inicialização completa gerando os asteróides.
        self.spawnAsteroids()

        #Inicializamos os efeitos sonoros que serão usados durante o jogo
        self.musictiro = loader.loadSfx('music/tiro.ogg')
        self.musictiro.setVolume(.1)
        self.musictiro.setLoopCount(1)

        self.musicdano = loader.loadSfx('music/dano.mp3')
        self.musicdano.setVolume(.3)
        self.musicdano.setLoopCount(1)

        self.musictrl = loader.loadSfx('music/trl.ogg')
        self.musictrl.setVolume(.3)
        self.musictrl.setLoopCount(0)
        self.musictrl.play()

        self.musicwin = loader.loadMusic('music/win.ogg')
        self.musicwin.setVolume(.5)
        self.musicwin.setLoopCount(1)

        self.musiclose = loader.loadMusic('music/lose.ogg')
        self.musiclose.setVolume(.5)
        self.musiclose.setLoopCount(1)

    # Conforme descrito anteriormente, isso simplesmente define
    # uma chave no dicionário self.keys para o valor fornecido.
    def setKey(self, key, val):
        self.keys[key] = val

    def setVelocity(self, obj, val):
        obj.setPythonTag("velocity", val)

    def getVelocity(self, obj):
        return obj.getPythonTag("velocity")

    def setExpires(self, obj, val):
        obj.setPythonTag("expires", val)

    def getExpires(self, obj):
        return obj.getPythonTag("expires")

    def reiniciajogo(self):
        global textfim1, textfim2, textpontemp
        textfim1.destroy()
        textfim2.destroy()
        textpontemp.destroy()
        imagefim.destroy()
        self.musictrl.play()
        ini = 0
        novapont(ini)
        self.alive = False
        for i in self.asteroids + self.bullets:
            i.removeNode()
        self.bullets = []  # Limpar a lista de asteroids
        self.ship.hide()  # Esconda a nave
        # Redefinir a velocidade
        self.setVelocity(self.ship, LVector3(0, 0, 0))
        Sequence(Wait(2),  # Aguarde 2 segundos
                 Func(self.ship.setR, 0),  # Redefinir título
                 Func(self.ship.setX, 0),  # Reinicializar a posição X
                 Func(self.ship.setZ, 0),  # Redefinir a posição Y (Z para Panda)
                 Func(self.ship.show),  # mostrar nave
                 Func(self.spawnAsteroids)).start()  # Refazer asteroids
        return Task.cont

    def spawnAsteroids(self):
        # Variável de controle para verificar se a nave está viva
        self.alive = True
        self.asteroids = []   # Lista que conterá nossos asteroides

        for i in range(10):
            # Isso carrega um asteroid. A textura escolhida é aleatória
            # de "asteroid1.png" para "asteroid3.png".
            asteroid = loadObject("asteroid%d.png" % (randint(1, 3)),
                                  scale=AST_INIT_SCALE)
            self.asteroids.append(asteroid)

            # Isso é meio que um hack, impede que os asteroids apareçam
            # perto do jogador. Cria a lista (-20, -19 ... -5, 5, 6, 7,
            # ... 20) e escolhe um valor a partir dele. Como o jogador começa em 0
            # e esta lista não contém nada de -4 a 4, não será
            # perto do jogador.
            asteroid.setX(choice(tuple(range(-SCREEN_X, -5)) + tuple(range(5, SCREEN_X))))
            # Mesma coisa para Y
            asteroid.setZ(choice(tuple(range(-SCREEN_Y, -5)) + tuple(range(5, SCREEN_Y))))

            # Heading é um ângulo aleatório em radianos
            heading = random() * 2 * pi

            # Converte o rumo em um vetor e o multiplica pela velocidade para
            # pegar um vetor velocidade
            v = LVector3(sin(heading), 0, cos(heading)) * AST_INIT_VEL
            self.setVelocity(self.asteroids[i], v)

    # Função para criar a tela de vitória
    def textwin(self):
        global ini, relo, textfim1, textfim2, textpontemp, imagefim

        self.musictrl.stop()
        self.musicwin.play()

        textfim1 = OnscreenText(text='Parabéns', pos=(0, 0.4),
                     fg=(1, 1, 1, 1), shadow=(0, 0, 0, 0.5), scale=0.15)

        textfim2 = OnscreenText(text='você destruiu todos os asteroids', pos=(0, 0.2),
                     fg=(1, 1, 1, 1), shadow=(0, 0, 0, 0.5), scale=0.15)

        textpontemp = OnscreenText(text='fez '+str(ini)+' pontos em '+str(relo)+' segundos',
                                   pos=(0, 0),fg=(1, 1, 1, 1), shadow=(0, 0, 0, 0.5), scale=0.15)

        imagefim = OnscreenImage(image='image/vasof.png', pos=(0, 0, -0.4), scale=.50)
        imagefim.setTransparency(TransparencyAttrib.MAlpha)

    # Função para criar a tela de derrota
    def textlose(self):
        global ini, relo, textfim1, textfim2, textpontemp, imagefim

        self.musictrl.stop()
        self.musiclose.play()

        textfim1 = OnscreenText(text='Infelizmente', pos=(0, 0.4),
                     fg=(1, 1, 1, 1), shadow=(0, 0, 0, 0.5), scale=0.15)

        textfim2 = OnscreenText(text='você perdeu', pos=(0, 0.2),
                     fg=(1, 1, 1, 1), shadow=(0, 0, 0, 0.5), scale=0.15)

        textpontemp = OnscreenText(text='fez ' + str(ini) + ' pontos em ' + str(relo) + ' segundos',
                                   pos=(0, 0),fg=(1, 1, 1, 1), shadow=(0, 0, 0, 0.5), scale=0.15)

        imagefim = OnscreenImage(image='image/vasot.png', pos=(0, 0, -0.4), scale=.50)
        imagefim.setTransparency(TransparencyAttrib.MAlpha)

    # Esta é a nossa principal função de tarefa, que faz o por-frame
    # em processamento. Leva em self como todas as funções em uma classe, e task,
    # o objeto de tarefa retornado por taskMgr.
    def gameLoop(self, task):
        global ini, relo, valor

        # Atualiza o tempo por frame
        relo = int(time.time() - valor)
        novorelo(relo)

        # Obtém o tempo decorrido desde o próximo quadro. Precisamos disso para o nosso
        # cálculos de distância e velocidade.
        dt = globalClock.getDt()

        # Se a nave não estiver vivo, não faça nada. Tarefas retornam Task.cont
        # significa que a tarefa deve continuar em execução. Se Task.done fosse
        # retornado em vez disso, a tarefa seria removida e não seria mais
        # chamou cada frame.
        if not self.alive:
            ini = 0
            novapont(ini)
            valor = time.time()
            return Task.cont

        # atualizar a posição da nave
        self.updateShip(dt)

        # verifique se a nave pode disparar
        if self.keys["fire"] and task.time > self.nextBullet:
            self.musictiro.play()
            self.fire(task.time)  # Se sim, chame a função fire
            # E desative o disparo um pouco
            self.nextBullet = task.time + BULLET_REPEAT
        # Desative a função fire até a próxima barra de espaço pressionada
        self.keys["fire"] = 0

        # Atualizar asteroids
        for obj in self.asteroids:
            self.updatePos(obj, dt)

        # Atualizar balas
        newBulletArray = []
        for obj in self.bullets:
            self.updatePos(obj, dt)  # Atualizar as listas de tiros
            # As balas têm um tempo de vida (ver definição em fire)
            # Se um marcador não expirou, adicione-o à nova lista de marcadores para
            # continuar existindo.
            if self.getExpires(obj) > task.time:
                newBulletArray.append(obj)
            else:
                obj.removeNode()  # Caso contrário, remova-o da cena.
        # Defina o array de marcadores para ser o array recém-atualizado
        self.bullets = newBulletArray

        # Verifique a colisão de balas com asteróides
        # Resumindo, ele verifica cada bala contra cada asteróide. Isto é
        # Bastante lento. Uma grande otimização seria ordenar os objetos deixados para
        # certo e verifique apenas se eles se sobrepõem. A taxa de quadros pode cair muito se
        # há muitas balas na tela, mas na maioria das vezes está tudo bem.
        for bullet in self.bullets:
            # Esta declaração de alcance faz passar pela lista de asteróides
            # para trás. Isso ocorre porque se um asteróide for removido, o
            # elementos depois dele mudarão de posição na lista. Se tu vais
            # para trás, o comprimento permanece constante.
            for i in range(len(self.asteroids) - 1, -1, -1):
                asteroid = self.asteroids[i]
                # A detecção de colisão do Panda é mais complicada do que precisamos
                # Esta é a verificação básica de colisão de esferas. Se o
                # distância entre os centros dos objetos é menor que a soma dos
                # raios dos dois objetos, então temos uma colisão. Nós usamos
                # lengthSquared() pois é mais rápido que length().
                if ((bullet.getPos() - asteroid.getPos()).lengthSquared() <
                    (((bullet.getScale().getX() + asteroid.getScale().getX())
                      * .5) ** 2)):
                    self.musicdano.play()
                    # Agendar o marcador para remoção
                    self.setExpires(bullet, 0)
                    self.asteroidHit(i)      # Função quando acertar um asteroid

        # Agora fazemos o mesmo passo de colisão para a nave
        shipSize = self.ship.getScale().getX()
        for ast in self.asteroids:
            # Verificação de colisão da nave contra o asteroide
            if ((self.ship.getPos() - ast.getPos()).lengthSquared() <
                    (((shipSize + ast.getScale().getX()) * .5) ** 2) - 3):
                # Se houver um acerto, limpe a tela e agende uma reinicialização
                self.alive = False
                self.textlose()
                for i in self.asteroids + self.bullets:
                    i.removeNode()
                self.bullets = []
                self.ship.hide()
                return Task.cont
        # Se o jogador destruiu com sucesso todos os asteróides, reapareça-os
        if len(self.asteroids) == 0:
            self.alive = False
            self.textwin()
            for i in self.asteroids + self.bullets:
                i.removeNode()
            self.bullets = []
            self.ship.hide()
            return Task.cont

        return Task.cont   # Como todos retornos é Task.cont, a tarefa
        #continua indefinidamente

    # Atualiza as posições dos objetos
    def updatePos(self, obj, dt):
        vel = self.getVelocity(obj)
        newPos = obj.getPos() + (vel * dt)

        # Verifica se o objeto está fora dos limites
        radius = .5 * obj.getScale().getX()
        if newPos.getX() - radius > SCREEN_X:
            newPos.setX(-SCREEN_X)
        elif newPos.getX() + radius < -SCREEN_X:
            newPos.setX(SCREEN_X)
        if newPos.getZ() - radius > SCREEN_Y:
            newPos.setZ(-SCREEN_Y)
        elif newPos.getZ() + radius < -SCREEN_Y:
            newPos.setZ(SCREEN_Y)

        obj.setPos(newPos)

    # A função para quando um asteróide é atingido por uma bala
    def asteroidHit(self, index):
        global ini
        # Se o asteróide for pequeno, ele é simplesmente removido
        if self.asteroids[index].getScale().getX() <= AST_MIN_SCALE:
            self.asteroids[index].removeNode()
            ini += 3
            novapont(ini)
            # Remova o asteroide da lista de asteroides.
            del self.asteroids[index]
        else:
            if self.asteroids[index].getScale().getX() < 2.9:
                ini += 2
                novapont(ini)
            if self.asteroids[index].getScale().getX() >= 2.9:
                ini += 1
                novapont(ini)

            # Se for grande o suficiente, divida-o em pequenos asteróides.
            # Primeiro atualizamos o asteroide atual.
            asteroid = self.asteroids[index]
            newScale = asteroid.getScale().getX() * AST_SIZE_SCALE
            asteroid.setScale(newScale)  # Realocar asteroid

            # A nova direção é escolhida como perpendicular à direção antiga
            # Isso é determinado usando o produto cruzado, que retorna um
            # vetor perpendicular aos dois vetores de entrada. Ao cruzar
            # velocidade com um vetor que entra na tela, obtemos um vetor
            # que é ortogonal à velocidade original no plano da tela.
            vel = self.getVelocity(asteroid)
            speed = vel.length() * AST_VEL_SCALE
            vel.normalize()
            vel = LVector3(0, 1, 0).cross(vel)
            vel *= speed
            self.setVelocity(asteroid, vel)

            # Agora criamos um novo asteroide idêntico ao atual
            newAst = loadObject(scale=newScale)
            self.setVelocity(newAst, vel * -1)
            newAst.setPos(asteroid.getPos())
            newAst.setTexture(asteroid.getTexture(), 1)
            self.asteroids.append(newAst)

    # Isso atualiza a posição do navio. Isso é semelhante à atualização geral
    # mas leva em conta giro e empuxo
    def updateShip(self, dt):
        heading = self.ship.getR()  # Heading é o valor de rolagem para este modelo
        # Muda o rumo se a esquerda ou a direita estiver sendo pressionada
        if self.keys["turnRight"]:
            heading += dt * TURN_RATE
            self.ship.setR(heading % 360)
        elif self.keys["turnLeft"]:
            heading -= dt * TURN_RATE
            self.ship.setR(heading % 360)

        # O empuxo causa aceleração na direção em que o navio está atualmente voltado
        if self.keys["accel"]:
            heading_rad = DEG_TO_RAD * heading
            # Isso cria um novo vetor de velocidade e o adiciona ao atual
            # em relação à câmera, a tela no Panda é o plano XZ.
            # Portanto, todos os nossos valores Y em nossas velocidades são 0 para significar
            # nenhuma mudança nessa direção.
            newVel = \
                LVector3(sin(heading_rad), 0, cos(heading_rad)) * ACCELERATION * dt
            newVel += self.getVelocity(self.ship)
            # Fixa a nova velocidade na velocidade máxima. comprimentoQuadrado() é
            # usado novamente, pois é mais rápido que length()
            if newVel.lengthSquared() > MAX_VEL_SQ:
                newVel.normalize()
                newVel *= MAX_VEL
            self.setVelocity(self.ship, newVel)

        # Finalmente, atualize a posição como em qualquer outro objeto
        self.updatePos(self.ship, dt)

    # Cria um tiro e o adiciona à lista de tiro
    def fire(self, time):
        direction = DEG_TO_RAD * self.ship.getR()
        pos = self.ship.getPos()
        bullet = loadObject("bullet.png", scale=.5)  # Cria a imagem do tiro
        bullet.setPos(pos)
        # A velocidade é em relação ao navio
        vel = (self.getVelocity(self.ship) +
               (LVector3(sin(direction), 0, cos(direction)) *
                BULLET_SPEED))
        self.setVelocity(bullet, vel)
        # Defina o tempo de expiração do tiro para um certo valor além da
        # hora atual
        self.setExpires(bullet, time + BULLET_LIFE)

        # Por fim, adicione o novo tiro à lista
        self.bullets.append(bullet)

# Agora temos tudo o que precisamos. Faça uma instância da classe e inicie a Renderização 3D

demo = AsteroidsIP()
demo.run()
