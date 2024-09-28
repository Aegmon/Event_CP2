import csv, time
from collections import namedtuple
from functools import partial
from random import choices, randint, randrange, random
from typing import List, Callable, Tuple

# Define the namedtuple
Thing = namedtuple('Thing', ['name', 'rating', 'price'])

# Define the CSV file paths
digital_printing = 'C:/Users/Adrian/Desktop/HTML Guide 2/Capstone/Experiment1/csvs/Digital_Printing.csv'

# Initialize lists to store namedtuples
digital_printing_arr = []

with open(digital_printing, mode='r', newline='') as csv_file:
    csv_reader = csv.DictReader(csv_file)
    for row in csv_reader:
        thing = Thing(name=row['name'], rating=int(row['rating']), price=float(row['price']))
        digital_printing_arr.append(thing)

digital_printing1 = digital_printing_arr

Genome = List[int]
Population = List[Genome]
FitnessFunc = Callable[[Genome], int]
PopulateFunc = Callable[[], Population]
SelectionFunc = Callable[[Population, FitnessFunc], Tuple[Genome, Genome]]
CrossoverFunc = Callable[[Genome, Genome], Tuple[Genome, Genome]]
MutationFunc = Callable[[Genome, int, float], Genome]

# Genome and population generation functions
def generate_genome_digital_printing(length: int) -> Genome:
    return choices([0, 1], k=length)

def generate_population_digital_printing(size: int, genome_length: int) -> Population:
    return [generate_genome_digital_printing(genome_length) for _ in range(size)]

def fitness_digital_printing(genome: Genome, digital_printing1: List[Thing], price_limit_digital_printing: int) -> int:
    if len(genome) != len(digital_printing1):
        raise ValueError("Genome and things list must be of the same length")

    price = 0
    rating = 0

    for i, thing in enumerate(digital_printing1):
        if genome[i] == 1:
            price += thing.price
            rating += thing.rating

    if price == 0:
        return 0  # Penalize genomes with zero price if necessary

    if price > price_limit_digital_printing:
        return 0  # Penalize genomes that exceed the price limit
    
    return rating

# Selection, crossover, and mutation_digital_printing functions
def selection_pair_digital_printing(population: Population, fitness_func: FitnessFunc) -> Population:
    return choices(
        population=population,
        weights=[fitness_func(genome) for genome in population],
        k=2
    )

def single_point_crossover_digital_printing(a: Genome, b: Genome) -> Tuple[Genome, Genome]:
    if len(a) != len(b):
        raise ValueError("Genomes a and b must be of the same length")

    length = len(a)
    if length < 2:
        return a, b

    p = randint(1, length - 1)
    return a[0:p] + b[p:], b[0:p] + a[p:]

def mutation_digital_printing(genome: Genome, num: int = 1, probability: float = 0.1) -> Genome:
    for _ in range(num):
        index = randrange(len(genome))
        genome[index] = genome[index] if random() > probability else abs(genome[index] - 1)
    return genome

def run_evolution_digital_printing(
        populate_func: PopulateFunc,
        fitness_func: FitnessFunc,
        fitness_limit_digital_printing: int,
        selection_func: SelectionFunc = selection_pair_digital_printing,
        crossover_func: CrossoverFunc = single_point_crossover_digital_printing,
        mutation_func: MutationFunc = mutation_digital_printing,
        generation_limit_digital_printing: int = 200
) -> Tuple[Population, int]:
    population = populate_func()

    for i in range(generation_limit_digital_printing):
        # Sort population by fitness_digital_printing
        population = sorted(
            population,
            key=lambda genome: fitness_func(genome),
            reverse=True
        )

        # Check if the best genome has reached the fitness_digital_printing limit
        best_fitness = fitness_func(population[0])
        if best_fitness >= fitness_limit_digital_printing:
            break

        next_generation = population[0:2]  # Elitism: carry over the best 2

        # Generate the rest of the next generation
        for j in range(int(len(population) / 2) - 1):
            parents = selection_func(population, fitness_func)
            offspring_a, offspring_b = crossover_func(parents[0], parents[1])
            offspring_a = mutation_func(offspring_a)
            offspring_b = mutation_func(offspring_b)
            next_generation += [offspring_a, offspring_b]

        population = next_generation

    return population, i

# Helper function to convert genome to list of things
def genome_to_things_digital_printing(genome: Genome, digital_printing1: List[Thing]) -> List[Thing]:
    result = []
    for i, thing in enumerate(digital_printing1):
        if genome[i] == 1:
            result.append(thing.name)
    return result

# # Parameters for price limit of 1000
# price_limit_digital_printing = 5000
# fitness_limit_digital_printing = 500  # Adjust fitness_digital_printing limit to reflect more restrictive price limit
# population_size_digital_printing = 20  # Increase population size for better exploration
# generation_limit_digital_printing = 200  # Increase generation limit for thorough search

# start = time.time()
# population, generations = run_evolution_digital_printing(
#     populate_func=partial(
#         generate_population_digital_printing, size=population_size_digital_printing, genome_length=len(digital_printing1)
#     ),
#     fitness_func=partial(
#         fitness_digital_printing, digital_printing1=digital_printing1, price_limit_digital_printing=price_limit_digital_printing
#     ),
#     fitness_limit_digital_printing=fitness_limit_digital_printing,
#     generation_limit_digital_printing=generation_limit_digital_printing
# )
# end = time.time()

# print(f"number of generations: {generations} ")
# print(f"time: {end - start}s")
# print(f"best solution: {genome_to_things_digital_printing(population[0], digital_printing1)}")

# digital_printing_answers = genome_to_things_digital_printing(population[0], digital_printing1)

# digital_printing_answers=[]