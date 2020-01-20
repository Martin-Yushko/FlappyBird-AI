import pygame
import neat
import time
import os
import random
pygame.font.init()

GEN = 0
SCENE_WIDTH = 500
SCENE_HEIGHT = 800
BIRD_IMGS = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird1.png"))), pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird2.png"))), pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird3.png")))]
PIPE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "pipe.png")))
BG_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bg.png")))
BASE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "base.png")))
MAX_VEL = 16
ANIMATION_TIME = 5
STAT_FONT = pygame.font.SysFont("comicsans", 54)


class Bird:
	IMGS = BIRD_IMGS
	MAX_ROT = 25
	ROT_VEL = 20


	def __init__(self, x, y):
		self.x = x
		self.y = y
		self.tilt = 0
		self.tick_count = 0
		self.vel = 0
		self.height = self.y
		self.img_count = 0
		self.img = self.IMGS[0]

	def jump(self):
		self.vel = -10
		self.tick_count = 0
		self.height = self.y


	def getDisplacement(self, vel, time):
		return vel*time + 1.5*time**2

	def move(self):
		self.tick_count += 1
		# distplacement of bird given by velocity & time in jump
		d = self.getDisplacement(self.vel, self.tick_count)

		if d >= MAX_VEL:
			d = MAX_VEL


		if d < 0:
			d -=2

		self.y = self.y + d

		if self.y < 0:
			self.y = 0

		def ShouldTiltUp(distplacement):
			return d < 0 or self.y < self.height + 50

		if ShouldTiltUp(d):
			if self.tilt < self.MAX_ROT:
				self.tilt = self.MAX_ROT
		else:
			if self.tilt > -90:
				self.tilt -= self.ROT_VEL


	def draw(self, scene):
		# animate wings of bird
		self.img_count += 1

		next_img_index = self.img_count % ANIMATION_TIME

		if next_img_index >= len(self.IMGS):
			next_img_index = 0
			self.img_count = 0

		self.img = self.IMGS[next_img_index]

		#render tilt of bird

		rotate_img = pygame.transform.rotate(self.img, self.tilt)
		#rotate img around center instead of top left as pivot
		new_rect = rotate_img.get_rect(center = self.img.get_rect(topleft = (self.x, self.y)).center)

		scene.blit(rotate_img, new_rect.topleft)


	def getMask(self):
		return pygame.mask.from_surface(self.img)

	def hitFloor(self):
		return self.y + self.img.get_height() >= SCENE_HEIGHT - 70

class Pipe:
	GAP = 200
	VEL =  5
	PIPE_BOTTOM = PIPE_IMG
	PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True)

	def __init__(self,x):
		self.x = x
		self.height = 0
		self.gap = 100
		self.top = 0
		self.bottom = 0
		self.passed = False
		self.setHeight()

	def setHeight(self):
		self.height = random.randrange(50, 450)
		self.top = self.height - self.PIPE_TOP.get_height()
		self.bottom = self.height + self.GAP

	def move(self):
		self.x -= self.VEL

	def draw(self, scene):
		scene.blit(self.PIPE_TOP, (self.x, self.top))
		scene.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

	def doesCollide(self, bird):
		bird_mask = bird.getMask()
		top_mask = pygame.mask.from_surface(self.PIPE_TOP)
		bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

		top_offset = (self.x - bird.x, int(self.top - round(bird.y)))
		bottom_offset = (self.x - bird.x, int(self.bottom - round(bird.y)))

		bottom_point = bird_mask.overlap(bottom_mask, bottom_offset)
		top_point = bird_mask.overlap(top_mask, top_offset)

		if bottom_point or top_point:
			return True

		return False

	def offScene(self):
		return self.x + self.PIPE_TOP.get_width() < 0

	def updatePass(self, bird):
		if not self.passed and self.x < bird.x:
			self.passed = True
			return True

		return False

class Base:
	VEL = 5
	WIDTH = BASE_IMG.get_width()
	IMG = BASE_IMG

	def __init__(self,y):
		self.y = y
		self.x1 = 0
		self.x2 = self.WIDTH

	def move(self):
		self.x1 -= self.VEL
		self.x2 -= self.VEL

		#cycle the two base imgs for rendering
		if self.x1 + self.WIDTH < 0:
			self.x1 = self.x2 + self.WIDTH

		if self.x2 + self.WIDTH < 0:
			self.x2 = self.x1 + self.WIDTH

	def draw(self, scene):
		scene.blit(self.IMG, (self.x1, self.y))
		scene.blit(self.IMG, (self.x2, self.y))



def drawScene(scene, birds, pipes, base, score, generation):
	scene.blit(BG_IMG, (0,0))

	for pipe in pipes:
		pipe.draw(scene)

	scoreText = STAT_FONT.render("Score: " + str(score), 1, (255,255,255))
	genText = STAT_FONT.render("Gen: " + str(generation), 1, (255,255,255))

	scene.blit(genText, (10, 10))
	scene.blit(scoreText, (SCENE_WIDTH - 10 - scoreText.get_width(), 10))

	base.draw(scene)

	for bird in birds:
		bird.draw(scene)
	pygame.display.update()


def main(genomes, config):
	global GEN 
	GEN += 1
	networks = []
	genes = []
	birds = []

	for _, g in genomes:
		net = neat.nn.FeedForwardNetwork.create(g, config)
		networks.append(net)
		birds.append(Bird(230, 350))
		g.fitness = 0
		genes.append(g)



	scene = pygame.display.set_mode((SCENE_WIDTH, SCENE_HEIGHT))
	clock = pygame.time.Clock()
	bird = Bird(230, 350)
	pipes = [Pipe(SCENE_WIDTH)]
	base = Base(SCENE_HEIGHT - 70)
	run = True
	score = 0

	while run:
		clock.tick(1000)
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				run = False
				pygame.quit()
				quit()


		pipe_of_interest = 0
		if len(birds) > 0:
			if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
				pipe_of_interest = 1
		else: 
		# no birds left, so quit
			run = False
			break

		for i, bird in enumerate(birds):
			bird.move()
			genes[i].fitness += 0.1
			if len(pipes) > 0:
				output = networks[i].activate((bird.y, abs(bird.y - pipes[pipe_of_interest].height)
													 , abs(bird.y - pipes[pipe_of_interest].bottom)))
			else:
				output = [0]

			if output[0] > 0.3:
				bird.jump()

		add_pipe = False
		remove = []
		for pipe in pipes:
			for i, bird in enumerate(birds):
				if pipe.doesCollide(bird):
					genes[i].fitness -= 1
					birds.pop(i)
					networks.pop(i)
					genes.pop(i)

				#updatePass updates the pass state of pipe and returns true if state changed
				if not pipe.passed:
					add_pipe = pipe.updatePass(bird)
			
			if pipe.offScene():
				remove.append(pipe)
			pipe.move()
		
		if add_pipe:
			score += 1

			for g in genes:
				g.fitness += 4

			pipes.append(Pipe(SCENE_WIDTH))

		for pipe in remove:
			pipes.remove(pipe)

		for i, bird in enumerate(birds):
			if bird.hitFloor():
				birds.pop(i)
				networks.pop(i)
				genes.pop(i)

		base.move()

		drawScene(scene, birds, pipes, base, score, GEN)



#stuff for NEAT

def run(config_path):
	config = neat.config.Config(neat.DefaultGenome, 
								neat.DefaultReproduction,
								neat.DefaultSpeciesSet, 
								neat.DefaultStagnation, 
								config_path)
	p = neat.Population(config)

	p.add_reporter(neat.StdOutReporter(True))
	stats = neat.StatisticsReporter()
	p.add_reporter(stats)
	winner = p.run(main, 50)

if __name__ == "__main__":
	local_dir = os.path.dirname(__file__)
	config_path = os.path.join(local_dir, "config.txt")
	run(config_path)



			






			







