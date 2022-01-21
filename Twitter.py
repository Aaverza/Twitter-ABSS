import random

from soil.agents import FSM, state, default_state, prob
from soil import Environment
import logging

affected_users = ['']
engaged_users = ['']


class UserAgent(FSM):
    defaults = {
        'prob_tweet': 0.5,
        'agent_type': "Neutral",
    }

    def __init__(self, environment, agent_id=0, state=()):
        super().__init__(environment=environment, agent_id=agent_id, state=state)
        topics = ["News", "Sports", "Science/Tech", "TV Shows/Movies", "Art", "Video Games", "Politics"]
        self.define_topics(topics)
        self['follows'] = random.randrange(int(self.env['total_agents']) * self.env['min_followers'],
                                           int(self.env['total_agents']) * self.env['max_followers'])
        if self['agent_type'] == 'News':
            self['follows'] = int(self.env['total_agents']) * self.env['max_followers']

        if str(self['agent_type']) == "Neutral":
            self['belief_value'] = random.uniform(0.375, 0.625)
            self['belief_value'] = round(self['belief_value'], 4)

    @default_state
    @state
    def init_followers(self):
        total_agents = len(self.get_agents())
        self.define_followers()
        self['prob_tweet'] = (self['follows'] - total_agents * self.env['min_followers']) / (
                total_agents * self.env['max_followers'] - total_agents * self.env['min_followers'])
        self.set_state(self.neutral)

    @state
    def neutral(self):
        if prob(self.env['prob_ext_influence'] * self.env['prob_fake_spread'] * self['belief_value']):
            self.infect()
        if prob(self.env['prob_ext_influence'] * self.env['prob_real_spread'] * (1-self['belief_value'])):
            self.cure()

        if prob(self['prob_tweet']):
            self['tweet'] = "Sending Neutral Tweet"
            affected_users.clear()
            engaged_users.clear()
            self.retweet("net")
            self.targeted_tweet("net")
            self['impression'] = len(affected_users)
            self['engaged'] = len(engaged_users)

        if 0.625 <= self['belief_value'] < 0.875:
            self.set_state(self.fake_believer)
        elif 0.125 <= self['belief_value'] < 0.375:
            self.set_state(self.truth_believer)

    @state
    def fake_believer(self):
        if prob(self.env['prob_ext_influence'] * self.env['prob_fake_spread'] * self['belief_value']):
            self.infect()
        if prob(self.env['prob_ext_influence'] * self.env['prob_real_spread'] * (1-self['belief_value'])):
            self.cure()

        if prob(self['prob_tweet']):
            if prob(self.env['prob_fake_spread'] * self['belief_value']):
                self['tweet'] = "Sending Fake News"
                affected_users.clear()
                engaged_users.clear()
                self.retweet("neg")
                self.targeted_tweet("neg")
                self['impression'] = len(affected_users)
                self['engaged'] = len(engaged_users)
            else:
                self['tweet'] = "Sending Neutral Tweet"
                affected_users.clear()
                engaged_users.clear()
                self.retweet("net")
                self.targeted_tweet("net")
                self['impression'] = len(affected_users)
                self['engaged'] = len(engaged_users)

        if 0.375 < self['belief_value'] < 0.625:
            self.set_state(self.neutral)
        elif 0.875 <= self['belief_value'] < 1:
            self.set_state(self.infected)

    @state
    def truth_believer(self):
        if prob(self.env['prob_ext_influence'] * self.env['prob_fake_spread'] * self['belief_value']):
            self.infect()
        if prob(self.env['prob_ext_influence'] * self.env['prob_real_spread'] * (1-self['belief_value'])):
            self.cure()

        if prob(self['prob_tweet']):
            if prob(self.env['prob_real_spread'] * (1 - self['belief_value'])):
                self['tweet'] = "Sending Official News"
                affected_users.clear()
                engaged_users.clear()
                self.retweet("pos")
                self.targeted_tweet("pos")
                self['impression'] = len(affected_users)
                self['engaged'] = len(engaged_users)
            else:
                self['tweet'] = "Sending Neutral Tweet"
                affected_users.clear()
                engaged_users.clear()
                self.retweet("net")
                self.targeted_tweet("net")
                self['impression'] = len(affected_users)
                self['engaged'] = len(engaged_users)

        if 0.375 < self['belief_value'] < 0.625:
            self.set_state(self.neutral)
        elif 0 <= self['belief_value'] < 0.125:
            self.set_state(self.vaccinated)

    @state
    def infected(self):
        if prob(self.env['prob_ext_influence'] * self.env['prob_fake_spread'] * self['belief_value']):
            self.infect()
        if prob(self.env['prob_ext_influence'] * self.env['prob_real_spread'] * (1-self['belief_value'])):
            self.cure()

        if prob(self['prob_tweet']):
            self['tweet'] = "Sending Fake News"
            affected_users.clear()
            engaged_users.clear()
            self.retweet("neg")
            self.targeted_tweet("neg")
            self['impression'] = len(affected_users)
            self['engaged'] = len(engaged_users)

        if 0.625 <= self['belief_value'] < 0.875:
            self.set_state(self.fake_believer)

    @state
    def vaccinated(self):
        if prob(self.env['prob_ext_influence'] * self.env['prob_fake_spread'] * self['belief_value']):
            self.infect()
        if prob(self.env['prob_ext_influence'] * self.env['prob_real_spread'] * (1-self['belief_value'])):
            self.cure()

        if prob(self['prob_tweet']):
            self['tweet'] = "Sending Official News"
            affected_users.clear()
            engaged_users.clear()
            self.retweet("pos")
            self.targeted_tweet("pos")
            self['impression'] = len(affected_users)
            self['engaged'] = len(engaged_users)

        if 0.125 <= self['belief_value'] < 0.375:
            self.set_state(self.truth_believer)

    def infect(self):
        if self['belief_value'] is None:
            pass
        elif self['belief_value'] < self.env['max_belief_value']:
            self['belief_value'] += self.env['belief_value_increase']
            self['belief_value'] = round(self['belief_value'], 4)
            if self['belief_value'] >= 1:
                self['belief_value'] = 0.9999

    def cure(self):
        if self['belief_value'] is None:
            pass
        elif self['belief_value'] > self.env['min_belief_value']:
            self['belief_value'] -= self.env['belief_value_increase']
            self['belief_value'] = round(self['belief_value'], 4)
            if self['belief_value'] <= 0:
                self['belief_value'] = 0.0001

    def state_change(self):
        if 0.375 < self['belief_value'] < 0.625:
            if self.state != self.neutral:
                self.set_state(self.neutral)
        elif 0.625 <= self['belief_value'] < 0.875:
            if self.state != self.fake_believer:
                self.set_state(self.fake_believer)
        elif 0.875 <= self['belief_value'] < 1:
            if self.state != self.infected:
                self.set_state(self.infected)
        elif 0.125 <= self['belief_value'] < 0.375:
            if self.state != self.truth_believer:
                self.set_state(self.truth_believer)
        elif 0 <= self['belief_value'] < 0.125:
            if self.state != self.vaccinated:
                self.set_state(self.vaccinated)

    def retweet(self, tweet_type):
        neighboring_agents = self.get_neighboring_agents()
        for neighbor in neighboring_agents:
            if neighbor in affected_users:
                continue
            affected_users.append(neighbor)

            if str(neighbor['agent_type']) == "News":
                continue
            elif str(neighbor['agent_type']) == "Deception":
                if tweet_type == "neg":
                    # engaged_users.append(neighbor)
                    if prob(neighbor['prob_tweet']*self.env['prob_fake_spread']):
                        neighbor.retweet("neg")
                continue
            elif str(neighbor['agent_type']) == "Neutral":
                if tweet_type == "neg":
                    if prob(self.env['prob_fake_spread'] * neighbor['belief_value']):
                        neighbor.infect()
                        engaged_users.append(neighbor)
                        if prob(neighbor['prob_tweet'] * neighbor['belief_value']):
                            neighbor.retweet("neg")
                elif tweet_type == "pos":
                    if prob(self.env['prob_real_spread'] * (1 - neighbor['belief_value'])):
                        neighbor.cure()
                        engaged_users.append(neighbor)
                        if prob(neighbor['prob_tweet'] * (1 - neighbor['belief_value'])):
                            neighbor.retweet("pos")
                elif tweet_type == "net":
                    if prob(neighbor['prob_tweet'] * self.env['prob_neutral_spread']):
                        neighbor.retweet("net")
                        engaged_users.append(neighbor)

    def targeted_tweet(self, tweet_type):
        if len(engaged_users) > len(self.env.get_agents()) * self.env['trending_number']:
            for agent in self.get_agents():
                if agent['topic'] == self['topic'] and agent not in affected_users and str(
                        agent['agent_type']) != "News" and str(agent['agent_type']) != "Deception":
                    if tweet_type == "neg":
                        if prob(self.env['prob_fake_spread'] * agent['belief_value']):
                            agent.infect()
                            if prob(agent['prob_tweet'] * agent['belief_value']):
                                agent.retweet("neg")
                    elif tweet_type == "pos":
                        if prob(self.env['prob_real_spread'] * (1 - agent['belief_value'])):
                            agent.cure()
                            if prob(agent['prob_tweet'] * (1 - agent['belief_value'])):
                                agent.retweet("pos")
                    elif tweet_type == "net":
                        if prob(agent['prob_tweet'] * self.env['prob_neutral_spread']):
                            agent.retweet("net")

    def define_topics(self, topics):
        self['topic'] = random.choice(topics)

    def define_followers(self):
        other_users = self.env.get_agents()

        random.shuffle(other_users)
        for user in other_users:
            if user == self or len(user.get_neighboring_agents()) >= user['follows']:
                continue
            if len(self.get_neighboring_agents()) >= self['follows']:
                break

            if self['topic'] == user['topic']:
                self.env.add_edge(self, user)
            # random chance of following a user that does not have the same topic
            elif prob(self.env['prob_nontopic_follow']):
                self.env.add_edge(self, user)
            # elif user['agent_type'] == "Deception" and self['agent_type'] == "Deception":
            # self.env.add_edge(self, user)


class DeceptionAgent(UserAgent):
    defaults = {
        'agent_type': "Deception",
    }

    @default_state
    @state
    def init_followers(self):
        total_agents = len(self.get_agents())
        self.define_followers()
        self['prob_tweet'] = (self['follows'] - total_agents * self.env['min_followers']) / (
                total_agents * self.env['max_followers'] - total_agents * self.env['min_followers'])
        self.set_state(self.deception)

    @state
    def deception(self):
        if prob(self['prob_tweet']):
            self['tweet'] = "Sending Fake News"
            affected_users.clear()
            engaged_users.clear()
            self.retweet("neg")
            self.targeted_tweet("neg")
            self['impression'] = len(affected_users)
            self['engaged'] = len(engaged_users)


class NewsAgent(UserAgent):
    defaults = {
        'prob_tweet': 0.9,
        'agent_type': "News",
    }

    @default_state
    @state
    def init_followers(self):
        self.define_followers()
        self.set_state(self.news)

    @state
    def news(self):
        if prob(self['prob_tweet']):
            self['tweet'] = "Sending Official News"
            affected_users.clear()
            engaged_users.clear()
            self.retweet("pos")
            self.targeted_tweet("pos")
            self['impression'] = len(affected_users)
            self['engaged'] = len(engaged_users)
