import random

import gym
import numpy as np
import torch


def seed(seed):
    torch.manual_seed(seed)
    np.random.seed(seed)
    random.seed(seed)


# Code based on:
# https://github.com/openai/baselines/blob/master/baselines/deepq/replay_buffer.py

# Simple replay buffer
class ReplayBuffer(object):
    def __init__(self, max_size=10000):
        self.storage = []
        self.max_size = max_size

    # Expects tuples of (state, next_state, action, reward, done)
    def add(self, state, next_state, controller_action, action, reward, done):
        if len(self.storage) < self.max_size:
            self.storage.append((state, next_state, controller_action, action, reward, done))
        else:
            # Remove random element in the memory beforea adding a new one
            self.storage.pop(random.randrange(len(self.storage)))
            self.storage.append((state, next_state, controller_action, action, reward, done))


    def sample(self, batch_size=100, flat=True):
        ind = np.random.randint(0, len(self.storage), size=batch_size)
        states, next_states, controller_actions, actions, rewards, dones = [], [], [], [], [], []

        for i in ind:
            state, next_state, controller_action, action, reward, done = self.storage[i]

            if flat:
                states.append(np.array(state, copy=False).flatten())
                next_states.append(np.array(next_state, copy=False).flatten())
            else:
                states.append(np.array(state, copy=False))
                next_states.append(np.array(next_state, copy=False))
            controller_actions.append(np.array(controller_action, copy=False))
            actions.append(np.array(action, copy=False))
            rewards.append(np.array(reward, copy=False))
            dones.append(np.array(done, copy=False))

        # state_sample, action_sample, next_state_sample, reward_sample, done_sample
        return {
            "state": np.stack(states),
            "next_state": np.stack(next_states),
            "controller_action": np.stack(controller_actions),
            "action": np.stack(actions),
            "reward": np.stack(rewards).reshape(-1,1),
            "done": np.stack(dones).reshape(-1,1)          
        }


def evaluate_policy(env, agent, device, eval_episodes=10, max_timesteps=500):
    agent.policy.actor.eval()
    agent.policy.critic.eval()

    avg_reward = 0.
    for i in range(eval_episodes):
        obs = env.reset()
        done = False
        step = 0
        while not done and step < max_timesteps:
            agent.publish_img(obs, evaluation=True)
            while not agent.callback_processed:
                continue

            agent.writer.add_scalar("eval.controller.action.v", np.abs(agent.controller_action[0]), step)
            agent.writer.add_scalar("eval.controller.action.omega", np.abs(agent.controller_action[1]), step)
            agent.writer.add_scalar("eval.rl.action.v", np.abs(agent.rl_action[0]), step)
            agent.writer.add_scalar("eval.rl.action.omega", np.abs(agent.rl_action[1]), step)

            obs, reward, done, _ = env.step(agent.action)
            avg_reward += reward
            step += 1

    avg_reward /= eval_episodes

    agent.policy.actor.train()
    agent.policy.critic.train()
    return avg_reward