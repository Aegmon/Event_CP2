import pandas as pd
import numpy as np
import random

# Load data from the CSV file
data = pd.read_csv('C:/Users/Adrian/Desktop/HTML Guide 2/Capstone/Experiment3/csvs/supplier_low.csv')

# Parameters
price_limit = 25000
max_items = 5  # Limit the number of selected items
population_size = 20
num_generations = 50
mutation_rate = 0.01

# Define the fitness function
def fitness(individual):
    total_price = np.sum(data['price'][individual])
    total_rating = np.sum(data['rating'][individual])
    num_selected = np.sum(individual)

    # Return a penalty for exceeding price limit or number of items
    if total_price > price_limit or num_selected > max_items:
        return 0  # Invalid solution (over budget or too many items)

    return total_rating

# Generate an initial population ensuring no more than max_items are selected
def create_population(size):
    population = []
    for _ in range(size):
        individual = np.zeros(len(data), dtype=int)
        indices = np.random.choice(len(data), size=random.randint(1, max_items), replace=False)
        individual[indices] = 1
        population.append(individual)
    return population

# Selection (tournament selection) with total price limit check
def select(population):
    tournament_size = 5
    selected = []
    for _ in range(len(population)):
        tournament = random.sample(population, tournament_size)
        # Filter valid individuals based on fitness and price limit
        valid_tournament = []
        for ind in tournament:
            if fitness(ind) > 0:
                total_price = np.sum(data['price'][ind])
                if total_price <= price_limit:
                    valid_tournament.append(ind)
        
        if valid_tournament:  # Ensure we have valid candidates to select from
            selected.append(max(valid_tournament, key=fitness))
        else:
            selected.append(random.choice(population))  # Fallback to random if all are invalid
    return selected

# Crossover (single-point crossover)
def crossover(parent1, parent2):
    point = random.randint(1, len(parent1) - 1)
    child1 = np.concatenate((parent1[:point], parent2[point:]))
    child2 = np.concatenate((parent2[:point], parent1[point:]))
    return child1, child2

# Mutation
def mutate(individual):
    if np.sum(individual) >= max_items:
        # Ensure mutation does not increase the number of selected items
        indices = np.where(individual == 1)[0]
        if indices.size > 0:
            idx_to_mutate = random.choice(indices)
            individual[idx_to_mutate] = 0  # Remove an item
    elif random.random() < mutation_rate:
        idx_to_add = random.choice(range(len(individual)))
        if individual[idx_to_add] == 0 and np.sum(individual) < max_items:
            individual[idx_to_add] = 1  # Add an item
    return individual

# Run the genetic algorithm
def genetic_algorithm():
    population = create_population(population_size)
    for generation in range(num_generations):
        population = select(population)
        next_population = []
        for i in range(0, population_size, 2):
            parent1 = population[i]
            parent2 = population[i + 1]
            child1, child2 = crossover(parent1, parent2)
            next_population.append(mutate(child1))
            next_population.append(mutate(child2))
        population = next_population

    # Get the best solution
    best_solution = max(population, key=fitness)
    selected_items = data.iloc[best_solution == 1]
    total_price = selected_items['price'].sum()
    total_rating = selected_items['rating'].sum()

    return selected_items, total_price, total_rating

# Execute the genetic algorithm
selected_items, total_price, total_rating = genetic_algorithm()

# Output results
print("Selected Items:")
print(selected_items)
print(f"Total Price: {total_price}")
print(f"Total Rating: {total_rating}")
