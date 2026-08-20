import random
import math

# tuning parameters
SIMULATION_ROUNDS = 5
ACTIONS = [0, 1, 2]  # modify based on game

# weights (can tune later)
W_REWARD = 0.6
W_RISK = 0.3
W_FUTURE = 0.1

# simple memory (global)
history = {
    "actions": [],
    "results": []
}

def update_history(action, result):
    history["actions"].append(action)
    history["results"].append(result)
    
    # keep last 10 only
    if len(history["actions"]) > 10:
        history["actions"].pop(0)
        history["results"].pop(0)

def get_win_rate():
    if len(history["results"]) == 0:
        return 0.5
    return sum(history["results"]) / len(history["results"])

def simulate_future(state, action):
    score = 0
    
    for _ in range(SIMULATION_ROUNDS):
        # random future assumption (lightweight)
        future_reward = random.random()
        future_risk = random.random()
        
        score += (future_reward - future_risk)
    
    return score / SIMULATION_ROUNDS

def calculate_score(reward, risk, future):
    return (reward * W_REWARD) - (risk * W_RISK) + (future * W_FUTURE)

def get_mode():
    win_rate = get_win_rate()
    
    if win_rate > 0.7:
        return "AGGRESSIVE"
    elif win_rate < 0.4:
        return "SAFE"
    else:
        return "BALANCED"

def evaluate_action(observation, action):
    
    
    reward = random.random()
    risk = random.random()
    
    future = simulate_future(observation, action)
    
    score = calculate_score(reward, risk, future)
    
    return score

def agent(observation, configuration):
    
    mode = get_mode()
    
    best_action = ACTIONS[0]
    best_score = -999
    
    for action in ACTIONS:
        score = evaluate_action(observation, action)
        
        # mode adjustment
        if mode == "AGGRESSIVE":
            score *= 1.2
        elif mode == "SAFE":
            score *= 0.8
        
        if score > best_score:
            best_score = score
            best_action = action
    
    # fake result tracking (replace with real feedback if available)
    result = 1 if random.random() > 0.5 else 0
    update_history(best_action, result)
    
    return best_action

# test run
obs = {}
config = {}

for i in range(5):
    action = agent(obs, config)
    print(f"Step {i}: Action ->", action)

import time

for step in range(5):
    action = agent({}, {})
    print(f"Step {step}: Action -> {action}")
    time.sleep(1)  # 👈 delay

import matplotlib.pyplot as plt

actions = []

for step in range(10):
    action = agent({}, {})
    actions.append(action)

plt.plot(actions)
plt.title("Bot Decisions Over Time")
plt.show()

