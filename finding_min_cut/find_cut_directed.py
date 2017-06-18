# !/usr/bin/env python
# Name :  Madhur Rawat
# Organization: IIIT Delhi
# Date : 15/12/16

'''
Find min node cut in graph
Either in country to country topology or in attacker to victim topology
Using either start AS or not
'''

from __future__ import division
import matplotlib.pyplot as plt
import itertools
import sys
import math
import argparse
import networkx as nx
from networkx.algorithms.connectivity import local_node_connectivity
from collections import defaultdict
from networkx.algorithms.connectivity import minimum_st_node_cut
from networkx.algorithms import approximation as approx
from networkx.algorithms.connectivity import (build_auxiliary_node_connectivity)
from networkx.algorithms.flow import build_residual_network

# Local imports
import constants
import min_cut_constants
from min_cut_utility import BFS
from min_cut_utility import print_path_if_reachable
from as_graph_utility import as_digraph
from as_graph_utility import is_reachable
from as_graph_utility import paths_between_st
from as_graph_utility import auxiliary_graph
from minimum_st_node_cut import multiple_minimum_st_node_cut
from minimum_st_node_cut import zero_capacity_residual_paths
from heuristic_min_st_node_cut_impl import defense_st_cut
from heuristic_min_st_node_cut_impl import defense_cut_non_induced
from heuristic_min_st_node_cut_impl import set_heuristic_weight


'''
"Usage: python prog.py -c <COUNTRY_CODE> -m <MODE> -s <S/N>"
"MODE:"
"   1: country all to all"
"   2: country to imp"
"<S/N> using start/ not using start"	
'''


class NodeCutDirected :

	def __init__(self,country_code, mode, using_start, heuristic) :
		self.COUNTRY_CODE = country_code
		self.HEURISTIC = heuristic
		if mode == "1":
			self.MODE_SUFFIX = "_country_all"
		elif mode == "2":
			self.MODE_SUFFIX = "_imp"

		if using_start == "S":
			self.USING_START = True
			print "USING_START " + str(self.USING_START)
		else:
			self.USING_START = False
			print "USING_START " + str(self.USING_START)	

		self.selected_domains = []

		'''Constants
		'''
		# 16bit AS to AS mapping
		self.BIT16_TO_AS_MAPPING = constants.TEST_DATA + 'cbgp_16bit2AS_caida_map.txt'
		
		self.DOMAINS = constants.DOMAINS
		
		# Indicates that path were received from CBGP and therefore 16bit mapping was done possibly.
		self.IS_CBGP=True
		print "Note: IS_CBGP="+str(self.IS_CBGP);


	def node_cut_to_important(self) :
		START = 'start'
		union = set()

		# Every time a new domain is added we will add the paths for it to already created graph
		G = nx.DiGraph()

		# Every time a new domain is added we need to update the pf_dict with new values for nodes.
		pf_dict = {}

		done = False
		while (done == False and (not len(self.selected_domains) == self.DOMAINS)):
			'''
			Input from user the important locations to which to draw graph to
			'''
			print "domains " + str(self.DOMAINS)
			print "options " + str(range(1, len(self.DOMAINS) + 1))
			selected_imp = raw_input("Enter space separated choice. Currently single choice only. 0 to EXIT? ")
			if selected_imp == '0' or selected_imp == 0:
				done = True
				continue
			
			if not selected_imp.isdigit() or (int(selected_imp) - 1) > (len(self.DOMAINS) - 1) or selected_imp in self.selected_domains:
				print "invalid selected_imp or already selected " + selected_imp
				continue

			self.selected_domains.append(selected_imp)

			domain = self.DOMAINS[int(selected_imp) - 1]
			domain_file = constants.TEST_DATA + self.COUNTRY_CODE + "/" + self.COUNTRY_CODE + '_' + domain + '.txt'

			# donot use. use all_dest_as instead from actual paths
			dest_as_list = []
			self.add_dest_as(domain_file, dest_as_list)

			PATH_FILE = constants.TEST_DATA + self.COUNTRY_CODE + "/" + self.COUNTRY_CODE + "_gao_cbgp_paths" + self.MODE_SUFFIX + "_" + self.DOMAINS[int(selected_imp) - 1] + ".txt"
			# PATH_FILE = constants.TEST_DATA + "IL_gao_cbgp_paths_country_all.txt"
			print "PATH_FILE " + PATH_FILE
			
			mapping_dict = self.get_mapping_dict(self.BIT16_TO_AS_MAPPING)

			if self.USING_START:
				(G, all_start_as, all_dest_as) = as_digraph(PATH_FILE, self.IS_CBGP, self.USING_START, mapping_dict, dest_as_list, G, pf_dict)
				for dest in all_dest_as:
					print 'START', START, 'dest', dest
					defense_cut = defense_st_cut(G, START, dest, self.HEURISTIC)
					print '* defense_cut', defense_cut
					print '*'*50
					union.update(defense_cut)
				print
				print union
				print "len(union) " + str(len(union))
				print
				print "len(G.nodes()) " + str(len(G.nodes()))
				print

				H = G.copy()
				H.remove_nodes_from(defense_cut)
				print 'is_reachable', is_reachable(G, START, dest)
				raw_input("Press any key to continue...")
				print

			else:
				(G, all_start_as, all_dest_as) = as_digraph(PATH_FILE, self.IS_CBGP, self.USING_START, mapping_dict, None, G, pf_dict)

				# predecessors = set()
				# for dest in all_dest_as:
				# 	for predecessor in G.predecessors(dest):
				# 		predecessors.add(predecessor)
				# print 'dest predecessors ', predecessors
				# print 'len dest predecessors ', len(predecessors)
				# exit()

				print
				print "len(all_start_as) " + str(len(all_start_as))
				print "len(all_dest_as) " + str(len(all_dest_as))
				print
				for i, AS in enumerate(all_start_as):
					for dest in all_dest_as:
						if not AS == dest :

							# use when all to all topology is used for all to important cutset.
							if not dest in dest_as_list:
								continue

							print i, 'AS', AS, 'dest', dest
							
							defense_cut = defense_st_cut(G, AS, dest)
							print '* defense_cut', defense_cut
							print '*'*50
							union.update(defense_cut)
							


							# print 'AS:', AS, ' dest:', dest
							# max_pf = float('-inf')
							# max_cut=()
							# st_cuts, single_st_cut, max_possible_combinations = multiple_minimum_st_node_cut(G, AS, dest)
							# print 'len(st_cuts)', len(st_cuts)
							# print 'single_st_cut', single_st_cut
							# if not max_possible_combinations == None and max_possible_combinations > min_cut_constants.MAXIMUM_POSSIBLE_COMBINATIONS_DIRECTED:
							# 	st_cuts = []
							# 	st_cuts.append(single_st_cut)
							# elif len(st_cuts) > min_cut_constants.MAXIMUM_ALLOWED_ST_CUTS_COMBINATIONS_DIRECTED:
							# 	st_cuts = []
							# 	st_cuts.append(single_st_cut)



							# for st_cut in st_cuts:
							# 	H = G.copy()
							# 	H.remove_nodes_from(st_cut)
							# 	if not is_reachable(H, AS, dest):

							# 		pf = 0
							# 		for cut_node in st_cut:
							# 			pf = pf + pf_dict[cut_node]
							# 		# print 'st_cut', st_cut,'pf', pf
							# 		if(pf > max_pf):
							# 			max_pf = pf
							# 			max_cut = st_cut
							# 			tie=False
							# 		elif (pf == max_pf) and pf>0:
							# 			tie=True
							# print str(i), 'max_cut', max_cut, 'max_pf', max_pf
							# print
							# union.update(max_cut)
							
							# raw_input("Press any key to continue...")
				print
				print union
				print "len(union) " + str(len(union))
				print
				print "len(G.nodes()) " + str(len(G.nodes()))
				print

				H = G.copy()
				H.remove_nodes_from(defense_cut)
				print 'is_reachable', is_reachable(G, AS, dest)
				raw_input("Press any key to continue...")
				print

	def node_cut_non_induced_to_important(self):
		done = False
		while (done == False and (not len(self.selected_domains) == self.DOMAINS)):
			'''
			Input from user the important locations to which to draw graph to
			'''
			print "domains " + str(self.DOMAINS)
			print "options " + str(range(1, len(self.DOMAINS) + 1))
			selected_imp = raw_input("Enter space separated choice. Currently single choice only. 0 to EXIT? ")
			if selected_imp == '0' or selected_imp == 0:
				done = True
				continue
			
			if not selected_imp.isdigit() or (int(selected_imp) - 1) > (len(self.DOMAINS) - 1) or selected_imp in self.selected_domains:
				print "invalid selected_imp or already selected " + selected_imp
				continue

			self.selected_domains.append(selected_imp)

			domain = self.DOMAINS[int(selected_imp) - 1]
			domain_file = constants.TEST_DATA + self.COUNTRY_CODE + "/" + self.COUNTRY_CODE + '_' + domain + '.txt'

			# donot use. use all_dest_as instead from actual paths
			dest_as_list = []
			self.add_dest_as(domain_file, dest_as_list)

			PATH_FILE = constants.TEST_DATA + self.COUNTRY_CODE + "/" + self.COUNTRY_CODE +"_gao_cbgp_paths" + self.MODE_SUFFIX + "_" + self.DOMAINS[int(selected_imp) - 1] + ".txt"
			print "PATH_FILE " + PATH_FILE

			defense_cut_non_induced(PATH_FILE, self.HEURISTIC)


	def node_cut_non_induced_to_all(self):
		PATH_FILE = constants.TEST_DATA + self.COUNTRY_CODE + "/" + self.COUNTRY_CODE + "_gao_cbgp_paths" + self.MODE_SUFFIX + ".txt"
		print "PATH_FILE " + PATH_FILE

		mapping_dict = self.get_mapping_dict(self.BIT16_TO_AS_MAPPING)
		
		defense_cut_non_induced(PATH_FILE, self.HEURISTIC)
			

	def node_cut_to_all(self) :
		PATH_FILE = constants.TEST_DATA + self.COUNTRY_CODE + "/" + self.COUNTRY_CODE  + "_gao_cbgp_paths" + self.MODE_SUFFIX + ".txt"
		print "PATH_FILE " + PATH_FILE

		mapping_dict = self.get_mapping_dict(self.BIT16_TO_AS_MAPPING)
		(G, all_start_as, all_dest_as) = as_digraph(PATH_FILE, self.IS_CBGP, self.USING_START, mapping_dict, None, None, None)
		set_heuristic_weight(G, self.HEURISTIC)
		A = auxiliary_graph(G)
		union = set()
		new_union = set()
		print 'len(G.nodes())', len(G.nodes())
		ASFILE = constants.TEST_DATA + self.COUNTRY_CODE + "/" + self.COUNTRY_CODE  + "_AS.txt"
		fi = open(ASFILE)
		asset = set()
		print 'G.nodes()', G.nodes()
		for line in fi:
			line = line.strip()
			AS = line[2:]
			asset.add(AS)
		for node in G.nodes():
			if node not in asset:
				print '$', node
		# exit()

		# Using Start in All to All case does not make much sense.
		if self.USING_START: 
			for dest in all_start_as:
				if dest in all_start_as:
					print START, dest
					st_cut = minimum_st_node_cut(G, START, dest, auxiliary=H, residual=R)
					len_st_cut = len(st_cut)
					print st_cut
					print len_st_cut
					print
					if len_st_cut <= 200:
						union.update(st_cut)
					else:
						union.add(dest)
				else:
					print "warning: graph does not have node : " + dest

		else:
			print
			print "len(all_start_as) " + str(len(all_start_as))
			print "len(all_dest_as) " + str(len(all_dest_as))
			print
			count = 0
			freq_of_node_in_cut = dict()

			# predecessors = set()
			# for dest in all_dest_as:
			# 	for predecessor in G.predecessors(dest):
			# 		predecessors.add(predecessor)
			# print 'dest predecessors ', predecessors
			# print 'len dest predecessors ', len(predecessors)
			# exit()
			counter = 0
			for i, AS in enumerate(all_start_as):
				for dest in all_dest_as:
					if not dest == AS:
						
						# Donot delete these test values for IL all.
						# AS = '5580'
						# dest = '12400'
						# AS = '5580'
						# dest = '20473'
						# AS = '12400'
						# dest = '2914'
						# AS = '12400'
						# dest = '174'

						# test S n T for unequal cardinality for st-cut by both method. IL country all
						# AS = '200742'
						# dest = '35435'

						# test SnT for edge in R and not in G. Issue was iteration over R edges not G edges
						# AS = '9071'
						# dest = '20841'
						
						print i, 'AS', AS, 'dest', dest
						H = A.copy()
						defense_cut = defense_st_cut(H, AS, dest)
						print '* defense_cut', defense_cut
						print '*'*50
						
						union.update(defense_cut)
						for node in defense_cut:
							if node in freq_of_node_in_cut:
								freq_of_node_in_cut[node] = freq_of_node_in_cut[node] + 1
							else:
								freq_of_node_in_cut[node] = 1
						
						# tot_weight = 0
						# for node in defense_cut:
						# 	print node, 'pf ',G.node[node]['path_frequency']
						# 	tot_weight = tot_weight+G.node[node][min_cut_constants.HEURISTIC_WEIGHT]
						# print tot_weight



						# from heuristic_min_st_node_cut_impl import set_heuristic_weight
						# set_heuristic_weight(G, [min_cut_constants.PATH_FREQUENCY])

						# max_pf = float('-inf')
						# max_cut=()
						# st_cuts, single_st_cut, max_possible_combinations = multiple_minimum_st_node_cut(G, AS, dest)
						
						# if not max_possible_combinations == None and max_possible_combinations > min_cut_constants.MAXIMUM_POSSIBLE_COMBINATIONS_DIRECTED:
						# 	st_cuts = []
						# 	st_cuts.append(single_st_cut)
						# elif len(st_cuts) > min_cut_constants.MAXIMUM_ALLOWED_ST_CUTS_COMBINATIONS_DIRECTED:
						# 	st_cuts = []
						# 	st_cuts.append(single_st_cut)
		

						# for st_cut in st_cuts:
						# 	H = G.copy()
						# 	H.remove_nodes_from(st_cut)

						# 	if not is_reachable(H, AS, dest):
						# 		pf = 0
						# 		for cut_node in st_cut:
						# 			pf = pf + pf_dict[cut_node]
						# 		print 'possible', st_cut,'pf', pf
						# 		if(pf > max_pf):
						# 			max_pf = pf
						# 			max_cut = st_cut
						# 			tie=False
						# 		elif (pf == max_pf) and pf>0:
						# 			tie=True
						
						# union.update(max_cut)
						# print '* max_cut', max_cut
						# tot_weight = 0
						# for node in max_cut:
						# 	print node, G.node[node]['path_frequency']
						# 	tot_weight = tot_weight + (1/G.node[node]['path_frequency'])
						# print tot_weight
						# raw_input("Press any key to continue..............................................................")
						# print

			print 'freq_of_node_in_cut', freq_of_node_in_cut
			H = G.copy()
			while(len(freq_of_node_in_cut) > 0):
				maxval = 0
				maxnode = ""
				for node in freq_of_node_in_cut:
					if freq_of_node_in_cut[node] > maxval:
						maxval = freq_of_node_in_cut[node]
						maxnode = node
				
				H.remove_nodes_from([maxnode])
				del freq_of_node_in_cut[maxnode]
				new_union.add(maxnode)
				reachable = False
				for i, AS in enumerate(all_start_as):
					for dest in all_dest_as:
						if not dest == AS:
							if AS in H.nodes() and dest in H.nodes():
								if is_reachable(H, AS, dest):
									reachable = True
									break
					if reachable:
						print 'Still reachable after removing ', maxnode
						break

				if not reachable:
					break

		H = G.copy()
		H.remove_nodes_from(new_union)
		for i, AS in enumerate(all_start_as):
			for dest in all_dest_as:
				if not dest == AS:
					if AS in H.nodes() and dest in H.nodes():
						if is_reachable(H, AS, dest):
							print 'is_reachable after removing new_union'
							break

		print 'union', union
		print "len(union) " + str(len(union))
		print
		print 'new_union', new_union
		print "len(new_union) " + str(len(new_union))
		print
		print "len(G.nodes()) " + str(len(G.nodes()))
		print
		raw_input("Press any key to continue...")
		print

	def get_mapping_dict(self, BIT16_TO_AS_MAPPING) :
		"""Save 16bit to AS mapping in a dict.
		"""
		mapping_dict=dict()
		if self.IS_CBGP:
			with open(BIT16_TO_AS_MAPPING) as fi:
				for line in fi:
					ll=line[:len(line)-1]
					splits=ll.split(' ')
					if not splits[0] in mapping_dict:
						mapping_dict[splits[0]]=splits[1]
		return mapping_dict

	def add_dest_as(self, domain_file, dest_as_list) :
		with open(domain_file) as fi:
			for line in fi:
				if not line[0] == "#":
					ll = line.strip()
					splits = ll.split(' ')
					if not splits[2] in dest_as_list:
						dest_as_list.append(splits[2])
		
		print


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description = 'find cut for defender in directed graph')
	parser.add_argument('-c', '--country_code', help='Country code for which cut is to be found', required = True)
	parser.add_argument('-m', '--mode', help='1: all to all. 2: all to imp', required = True)
	parser.add_argument('-s', '--using_start', help='S:attach attacker nodes to START N:Donot use START', required = True)
	parser.add_argument('-H', '--heuristic', help='Interger value for heuristic to use', required = False)
	parser.add_argument('-i', '--induced', help='N: Donot use induced graph approach', required = False)

	# mode: 
	# 	1: all to all
	# 	2: all non important to important
	# 	3: non induced cut


	# CUSTOMER_DEGREE = 1
	# PROVIDER_DEGREE = 2
	# PEER_DEGREE = 3
	# CUSTOMER_CONE_SIZE = 4
	# ALPHA_CENTRALITY = 5
	# BETWEENNESS_CENTRALITY = 6
	# PATH_FREQUENCY = 7
	
	args = parser.parse_args()
	COUNTRY_CODE = args.country_code
	MODE = args.mode
	using_start = args.using_start
	heuristic = args.heuristic
	if not heuristic == None:
		heuristic = int(heuristic)
	induced = args.induced



	NC = NodeCutDirected(COUNTRY_CODE, MODE, using_start, heuristic)

	# Call node cut implementation
	if induced == None:
		print 'Using Induced DiGraph'
		if MODE == "2":
			NC.node_cut_to_important()
		elif MODE == "1":
			NC.node_cut_to_all()

	elif induced == 'n' or induced == 'N':
		if MODE == "2":
			NC.node_cut_non_induced_to_important()
		elif MODE == "1":
			NC.node_cut_non_induced_to_all()





	



	



