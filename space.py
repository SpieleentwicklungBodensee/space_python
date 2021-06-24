#!/usr/bin/env python3

import urllib
import json
import http.cookiejar
import time

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
urllib.request.install_opener(opener)

req = urllib.request.Request('https://xrrawva.com/space/')
urllib.request.urlopen(req).read()
playerId = cj._cookies['xrrawva.com']['/space']['playerId'].value

def sendInput(cmd):
    global lastInput
    data = json.dumps({'data0': playerId, 'data1': str(cmd)}).encode()
    req = urllib.request.Request('https://xrrawva.com/space/input.php', data=data, method='POST')
    try:
        urllib.request.urlopen(req)
        lastInput = time.time()
    except OSError:
        pass

def retrieveTileImage(tileId):
    req = urllib.request.urlopen('https://xrrawva.com/space/%i.png' % tileId)
    return io.BytesIO(req.read())

def retrieveWorld():
    req = urllib.request.urlopen('https://xrrawva.com/space/world.php')
    return json.loads(req.read())   

#---

import pygame
import io, sys

tileSize = 12
worldSize = 42, 42

pygame.init()

#screen = pygame.display.set_mode((worldSize[0] * tileSize, worldSize[1] * tileSize))

displayInfo = pygame.display.Info()
sceenSize = displayInfo.current_w, displayInfo.current_h
screen = pygame.display.set_mode(sceenSize, pygame.FULLSCREEN)

tileSize = min(sceenSize[0] // worldSize[0], sceenSize[1] // worldSize[1])
worldOffset = ((sceenSize[0] - tileSize * worldSize[0]) // 2,
               (sceenSize[1] - tileSize * worldSize[1]) // 2)

tiles = []
for i in range(12):
    tile = pygame.image.load(retrieveTileImage(i)).convert_alpha()
    tiles.append(pygame.transform.smoothscale(tile, (tileSize, tileSize)))

pygame.joystick.init()

for i in range(pygame.joystick.get_count()):
    pygame.joystick.Joystick(i).init()

pygame.mouse.set_visible(False)

lastInput = None
lastUpdate = None
world = {'o': []}

clock = pygame.time.Clock()

while True:
    for e in pygame.event.get():
        if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
            pygame.quit()
            sys.exit(0)

        if e.type == pygame.JOYAXISMOTION:
            if abs(e.value) > 0.5:
                if e.axis == 0:
                    sendInput('r' if e.value > 0 else 'l')
                elif e.axis == 1:
                    sendInput('d' if e.value > 0 else 'u')
        elif e.type == pygame.JOYBUTTONDOWN and e.joy < 2 and e.button < 6:
            sendInput(e.joy * 6 + e.button)

    curentTime = time.time()
    if lastInput is None or curentTime - lastInput > 10:
        sendInput('x')

    if lastUpdate is None or curentTime - lastUpdate > 0.5:
        try:
            world = retrieveWorld()
        except (ValueError, OSError):
            pass
        lastUpdate = curentTime

    screen.fill((0, 0, 0))

    for player in world['o']:
        pos = player['x'], player['y']
        color = [int(c) for c in player['c'].split(',')]

        for ty in range(3):
            for tx in range(3):
                tileId = player['t%i' % (ty * 3 + tx)]
                if tileId == 0:
                    continue

                p = ((pos[0] + tx) * tileSize + worldOffset[0],
                     (pos[1] + ty) * tileSize + worldOffset[1])
                r = pygame.Rect(p, (tileSize, tileSize))
                pygame.draw.rect(screen, color, r)

                screen.blit(tiles[tileId], p)

    pygame.display.flip()

    clock.tick(60)
