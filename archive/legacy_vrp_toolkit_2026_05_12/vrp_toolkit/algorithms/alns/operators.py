"""Removal and repair operators for ALNS algorithm.

This module contains the RemovalOperators and RepairOperators classes used
by the ALNS solver for PDPTW problems with battery constraints.
"""

from copy import deepcopy
import numpy as np
import random


class NodeNotFoundError(Exception):
    """Exception raised when a node is not found in any route."""
    def __init__(self, node):
        super().__init__(f"Node {node} not found in any route.")


# remove algorithm
class RemovalOperators:
    '''
    1.shaw removal
    -  calculate_similarity
    -  get_arrival_time
    2.random removal
    3.worst removal
    - calculate_contribution
    4.remove_requests
    '''

    def __init__(self, solution):
        self.solution = solution
        self.instance = solution.instance

        # Compatibility layer for VRPProblem interface
        self._distance_matrix = self._get_distance_matrix()
        self._time_matrix = self._get_time_matrix()
        self._n = self.instance.num_orders if hasattr(self.instance, 'num_orders') else self.instance.n

        # Start of SISR removal

    def _get_distance_matrix(self):
        """Get distance matrix with backward compatibility."""
        # Try interface method first
        if hasattr(self.instance, 'get_distance_matrix'):
            matrix = self.instance.get_distance_matrix()
            if matrix is not None:
                return matrix

        # Fallback to direct attribute
        if hasattr(self.instance, 'distance_matrix'):
            return self.instance.distance_matrix

        # Last resort: build from individual calls
        n = self.instance.num_nodes if hasattr(self.instance, 'num_nodes') else len(self.instance.indices)
        import numpy as np
        matrix = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                matrix[i][j] = self.instance.get_distance(i, j)
        return matrix

    def _get_time_matrix(self):
        """Get time matrix with backward compatibility."""
        # Try interface method first
        if hasattr(self.instance, 'get_time_matrix'):
            matrix = self.instance.get_time_matrix()
            if matrix is not None:
                return matrix

        # Fallback to direct attribute
        if hasattr(self.instance, 'time_matrix'):
            return self.instance.time_matrix

        # Last resort: build from individual calls
        n = self.instance.num_nodes if hasattr(self.instance, 'num_nodes') else len(self.instance.indices)
        import numpy as np
        matrix = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                matrix[i][j] = self.instance.get_time(i, j)
        return matrix

    # Main SISR removal function
    def SISR_removal(self, num_remove=None, L_max=None, avg_remove_order=None, d_matrix=None):
        """SISR (String-based Iterative String Removal) operator.

        Args:
            num_remove: Number of requests to remove (not used, for API compatibility)
            L_max: Maximum string length (default: use self.L_max if available, else 5)
            avg_remove_order: Average removal order (default: use self.avg_remove_order if available, else 2.0)
            d_matrix: Distance matrix (default: use self.d_matrix or self._distance_matrix)

        Returns:
            Modified solution with requests removed
        """
        # Use defaults if not provided
        if L_max is None:
            L_max = getattr(self, 'L_max', 5)
        if avg_remove_order is None:
            avg_remove_order = getattr(self, 'avg_remove_order', 2.0)
        if d_matrix is None:
            d_matrix = getattr(self, 'd_matrix', self._distance_matrix)

        remaining_orders = self.solution.unvisited_requests
        routes_copy = deepcopy(self.solution.routes)
        n_orders = self._n
        removed_list = []
        deconstructed_route_list = []
        k_s, l_s_max = self.number_of_strings(L_max, avg_remove_order, routes_copy, n_orders)
        k_s = min(k_s, len(routes_copy))
        for i in range(int(k_s)):
            if i == 0:
                start_order = int(self.order_to_start(n_orders, remaining_orders))
                # while any(start_order in sublist for sublist in routes_copy) is False:
                #     start_order = int(self.order_to_start(n_orders))
                route = self.find_lists_containing_element(routes_copy, start_order)
                l_t = self.number_of_orders(l_s_max, route)
                routes_copy, removed_list, deconstructed_route_list, primal_sorted_indices = self.primal_string_removal(
                    d_matrix, routes_copy, route, l_t, start_order, n_orders, removed_list, deconstructed_route_list)
            elif primal_sorted_indices == []:
                break
            else:
                route, next_order = self.find_next_list(primal_sorted_indices, routes_copy, remaining_orders)
                if route == []:
                    break
                l_t = self.number_of_orders(l_s_max, route)
                routes_copy, removed_list, deconstructed_route_list, primal_sorted_indices = self.other_string_removal(
                    d_matrix, routes_copy, route, l_t, next_order, n_orders, removed_list, deconstructed_route_list,
                    primal_sorted_indices)

        remaining_routes = deconstructed_route_list + routes_copy
        removed_list = removed_list  # + remaining_orders

        return self.remove_requests(removed_list)

    def number_of_strings(self, L_max, avg_remove_order, routes, n_orders):
        T_avg = np.floor(n_orders / len(routes))
        l_s_max = min(T_avg, L_max)
        k_s_max = 4 * avg_remove_order / (1 + l_s_max) - 1
        k_s = np.floor(np.random.uniform(1, k_s_max + 1))

        return k_s, l_s_max

    # Generate number of orders to remove in each string
    def number_of_orders(self, l_s_max, route):
        l_t_max = min(l_s_max, (len(route) - 2) / 2)
        l_t = np.floor(np.random.uniform(1, l_t_max + 1))

        return l_t

    # Generate random order to start, remove orders according to order distance matrix
    def order_to_start(self, n_orders, remaining_order):
        reference_order = np.floor(np.random.uniform(1, n_orders + 1))
        # if remaining_order != None:
        while reference_order in remaining_order:
            reference_order = np.floor(np.random.uniform(1, n_orders + 1))
        return reference_order

    def find_lists_containing_element(self, routes, order):
        return [route for route in routes if order in route][0]

    def primal_string_removal(self, d_matrix, routes, route, l_t, reference_order, n_orders, removed_list,
                              deconstructed_route_list):
        distances = d_matrix[reference_order - 1]
        sorted_indices = np.argsort(distances).tolist()
        # print('sorted_indices',sorted_indices)
        # sorted_indices_updated = sorted_indices.copy()
        route_1 = deepcopy(route)
        a = 0
        for i in sorted_indices:
            if a <= l_t - 1:
                if i + 1 in route:
                    route_1.remove(i + 1)
                    removed_list.append(i + 1)
                    route_1.remove(i + 1 + n_orders)
                    removed_list.append(i + 1 + n_orders)
                a += 1
            else:
                break
        for order in route[1:-1]:
            if order > n_orders:
                continue
            else:
                sorted_indices.remove(order - 1)
        routes.remove(route)

        deconstructed_route_list.append(route_1)
        # print('deconstructed_route_list',deconstructed_route_list)

        return routes, removed_list, deconstructed_route_list, sorted_indices

    def find_next_list(self, primal_sorted_indices, routes, remaining_order):
        d = 0
        # print('routes:',routes)
        # print('primal_sorted_indices',primal_sorted_indices)
        i = primal_sorted_indices[d]
        next_order = i + 1
        # print('next_order',next_order)
        # if remaining_order != None:
        while (next_order in remaining_order) and d < len(remaining_order) - 1:
            print(primal_sorted_indices)
            d = d + 1
            i = primal_sorted_indices[d]
            next_order = i + 1
        # while any(next_order in sublist for sublist in routes) is False:
        #             next_order = i + 1
        if d == len(remaining_order) - 1 and len(remaining_order) > 0:
            return [], None
        else:
            return [route for route in routes if next_order in route][0], next_order

    def other_string_removal(self, d_matrix, routes, route, l_t, reference_order, n_orders, removed_list,
                             deconstructed_route_list, primal_sorted_indices):
        distances = d_matrix[reference_order - 1]
        sorted_indices = np.argsort(distances).tolist()
        route_1 = deepcopy(route)
        a = 0
        for i in sorted_indices:
            if a <= l_t - 1:
                if i + 1 in route:
                    route_1.remove(i + 1)
                    removed_list.append(i + 1)
                    route_1.remove(i + 1 + n_orders)
                    removed_list.append(i + 1 + n_orders)
                a += 1
            else:
                break
        # route_2 = deepcopy(route)
        for order in route[1:-1]:
            if order > n_orders:
                continue
            else:
                primal_sorted_indices.remove(order - 1)
        routes.remove(route)

        deconstructed_route_list.append(route_1)

        return routes, removed_list, deconstructed_route_list, primal_sorted_indices

    # Lowercase alias for backward compatibility
    def sisr_removal(self, *args, **kwargs):
        """Alias for SISR_removal (lowercase for backward compatibility)."""
        return self.SISR_removal(*args, **kwargs)

    # *****************************************************************************************
    # End of SISR removal

    # *****************************************************************************************************
    # Start of shaw removal
    def shaw_removal(self, num_remove, p=None):
        """Shaw removal operator.

        Args:
            num_remove: Number of requests to remove
            p: Shaw removal parameter (default: use self.p if available, else 4.0)

        Returns:
            Modified solution with requests removed
        """
        # Use default p if not provided
        if p is None:
            p = getattr(self, 'p', 4.0)

        removed_requests = []
        remaining_requests = list(self.solution.visited_requests)

        if not remaining_requests:
            return self.solution  # No requests to remove

        # Select a request randomly
        initial_request = random.choice(remaining_requests)
        removed_requests.append(initial_request)
        remaining_requests.remove(initial_request)

        # Normalization factor
        max_distance = np.max(self._distance_matrix)
        max_arrive_time = np.max([np.max(arrival_time) for arrival_time in self.solution.route_arrival_times])

        while len(removed_requests) < num_remove and remaining_requests:
            last_removed = random.choice(removed_requests)
            L = [req for req in remaining_requests]
            L.sort(key=lambda req: self.calculate_similarity(last_removed, req, max_distance, max_arrive_time))

            y = random.random()
            selected_request = L[int(y ** p * len(L))]
            removed_requests.append(selected_request)
            remaining_requests.remove(selected_request)

        return self.remove_requests(removed_requests)

    def calculate_similarity(self, req1, req2, max_distance, max_arrive_time):
        '''for shaw_removal'''
        pickup1, delivery1 = req1, req1 + self._n
        pickup2, delivery2 = req2, req2 + self._n

        dist_pickup = self._distance_matrix[pickup1][pickup2] / max_distance
        dist_delivery = self._distance_matrix[delivery1][delivery2] / max_distance

        arrival_time_pickup = (self.get_arrival_time(pickup1) - self.get_arrival_time(pickup2)) / max_arrive_time
        arrival_time_delivery = (self.get_arrival_time(delivery1) - self.get_arrival_time(delivery2)) / max_arrive_time

        return dist_pickup + dist_delivery + arrival_time_pickup + arrival_time_delivery

    def get_arrival_time(self, node):
        '''
        for shaw_removal
        get the arrival time of the node
        '''
        for vehicle_id, route in enumerate(self.solution.routes):
            if node in route:
                return self.solution.route_arrival_times[vehicle_id][route.index(node)]
        raise NodeNotFoundError(node)

    # *****************************************************************************************************
    # End of shaw removal

    # *****************************************************************************************************
    # Start of random removal
    def random_removal(self, num_remove):
        remaining_requests = list(self.solution.visited_requests)
        # Limit num_remove to available requests
        actual_num_remove = min(num_remove, len(remaining_requests))
        if actual_num_remove == 0:
            return self.solution  # No requests to remove
        removed_requests = random.sample(remaining_requests, actual_num_remove)
        return self.remove_requests(removed_requests)

    # *****************************************************************************************************
    # End of random removal

    # *****************************************************************************************************
    # Start of worst removal
    def worst_removal(self, num_remove):
        remaining_requests = list(self.solution.visited_requests)
        contributions = [(req, self.calculate_contribution(req)) for req in remaining_requests]
        contributions.sort(key=lambda x: x[1], reverse=True)
        removed_requests = [req for req, _ in contributions[:num_remove]]
        # print(contributions)
        return self.remove_requests(removed_requests)

    def calculate_contribution(self, req):
        '''for  worst_removal'''
        temp_solution = deepcopy(self.solution)
        pickup, delivery = req, req + self._n

        # remove the pickup and delivery points
        for route in temp_solution.routes:
            if pickup in route:
                route.remove(pickup)
                route.remove(delivery)

        # update
        temp_solution.update_all()
        original_objective = self.solution.objective_function()
        new_objective = temp_solution.objective_function()

        # calculate the contribution
        contribution = original_objective - new_objective
        return contribution
        # *****************************************************************************************************
        # End of worst removal

    def remove_requests(self, requests_or_solution, requests=None):
        """Remove requests from solution.

        Args:
            requests_or_solution: Either requests list or solution (for backward compatibility)
            requests: Requests list (if first arg is solution)

        Returns:
            Modified solution with requests removed
        """
        # Handle backward compatibility: remove_requests(solution, requests) or remove_requests(requests)
        if requests is not None:
            # Called with (solution, requests) - ignore first arg, use self.solution
            requests_to_remove = requests
        else:
            # Called with just (requests)
            requests_to_remove = requests_or_solution

        new_solution = deepcopy(self.solution)
        # removed_pairs = []

        for request in requests_to_remove:
            pickup_node, delivery_node = request, request + self._n
            for route in new_solution.routes:
                if pickup_node in route:
                    route.remove(pickup_node)
                # Delivery node might be in a different route
                if delivery_node in route:
                    route.remove(delivery_node)

            # removed_pairs.append((pickup_node, delivery_node))
            new_solution.update_all()  # update all of the things

        # return new_solution, removed_pairs
        return new_solution




# insertion algorithm
class RepairOperators:
    def __init__(self, solution):
        # Store reference to solution (not deepcopy) to allow tests to verify identity
        # Note: greedy_insertion and regret_insertion will create copies as needed
        self.solution = solution
        self.instance = solution.instance
        # Compatibility layer for VRPProblem interface
        self._n = self.instance.num_orders if hasattr(self.instance, 'num_orders') else self.instance.n

        # Add compatibility attributes for tests
        self._distance_matrix = self._get_distance_matrix()
        self._time_matrix = self._get_time_matrix()

        self.insertion_log = []  # record

    def _get_distance_matrix(self):
        """Get distance matrix with backward compatibility."""
        # Try interface method first
        if hasattr(self.instance, 'get_distance_matrix'):
            matrix = self.instance.get_distance_matrix()
            if matrix is not None:
                return matrix

        # Fallback to direct attribute
        if hasattr(self.instance, 'distance_matrix'):
            return self.instance.distance_matrix

        # Last resort: build from individual calls
        n = self.instance.num_nodes if hasattr(self.instance, 'num_nodes') else len(self.instance.indices)
        import numpy as np
        matrix = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                matrix[i][j] = self.instance.get_distance(i, j)
        return matrix

    def _get_time_matrix(self):
        """Get time matrix with backward compatibility."""
        # Try interface method first
        if hasattr(self.instance, 'get_time_matrix'):
            matrix = self.instance.get_time_matrix()
            if matrix is not None:
                return matrix

        # Fallback to direct attribute
        if hasattr(self.instance, 'time_matrix'):
            return self.instance.time_matrix

        # Last resort: build from individual calls
        n = self.instance.num_nodes if hasattr(self.instance, 'num_nodes') else len(self.instance.indices)
        import numpy as np
        matrix = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                matrix[i][j] = self.instance.get_time(i, j)
        return matrix

    # *****************************************************************************************************
    # Start of greedy insertion
    def greedy_insertion(self, removed_pairs_or_solution, unvisited_requests=None):
        """Greedy insertion repair operator.

        Args:
            removed_pairs_or_solution: Either list of (pickup, delivery) pairs or a solution
            unvisited_requests: List of unvisited request IDs (if first arg is solution)

        Returns:
            Modified solution with requests inserted
        """
        # Handle backward compatibility
        if unvisited_requests is not None:
            # Called with (solution, unvisited_requests) - update self.solution and convert to pairs
            if hasattr(removed_pairs_or_solution, 'routes'):
                self.solution = removed_pairs_or_solution
            # Convert unvisited requests to removed_pairs
            removed_pairs = [(req, req + self._n) for req in unvisited_requests]
        else:
            # Called with just removed_pairs
            removed_pairs = removed_pairs_or_solution

        # loop the removed pairs
        for pickup, delivery in removed_pairs:
            best_cost = float('inf')
            best_route = None
            best_insert_position = None
            # loop each route to find a suitable location to insert
            temp_solution = deepcopy(self.solution)
            for vehicle_id, route in enumerate(self.solution.routes):
                for i in range(1, len(route)):
                    for j in range(i, len(route)):
                        temp_route = route[:i] + [pickup] + route[i:j] + [delivery] + route[j:]
                        # temp_solution = deepcopy(self.solution)
                        temp_solution.routes[vehicle_id] = temp_route
                        temp_solution.update_all()

                        if temp_solution.is_feasible():
                            cost = temp_solution.objective_function()
                            if cost < best_cost:
                                best_cost = cost
                                best_route = vehicle_id
                                best_insert_position = (i, j)

            # update the self.solution
            if best_route is not None and best_insert_position is not None:
                self.insert_single_request(pickup, delivery, best_route, best_insert_position)

        return self.solution

    # *****************************************************************************************************
    # End of greedy insertion

    # *****************************************************************************************************
    # Start of regret insertion
    def regret_insertion(self, removed_pairs_or_solution, unvisited_requests_or_k=None, k=3):
        """Regret insertion repair operator.

        Args:
            removed_pairs_or_solution: Either list of (pickup, delivery) pairs or a solution
            unvisited_requests_or_k: Either list of unvisited request IDs, or k parameter (integer)
            k: Regret parameter (default: 3)

        Returns:
            Modified solution with requests inserted
        """
        # Handle backward compatibility - multiple call signatures:
        # regret_insertion(removed_pairs, k) - old API
        # regret_insertion(solution, unvisited_requests, k) - test API
        # regret_insertion(removed_pairs) - minimal API

        if unvisited_requests_or_k is not None:
            if isinstance(unvisited_requests_or_k, int):
                # Called with (removed_pairs, k)
                removed_pairs = removed_pairs_or_solution
                k = unvisited_requests_or_k
            else:
                # Called with (solution, unvisited_requests, k)
                if hasattr(removed_pairs_or_solution, 'routes'):
                    self.solution = removed_pairs_or_solution
                # Convert unvisited requests to removed_pairs
                removed_pairs = [(req, req + self._n) for req in unvisited_requests_or_k]
        else:
            # Called with just (removed_pairs) or (removed_pairs, None, k)
            removed_pairs = removed_pairs_or_solution

        while removed_pairs:
            insertion_costs = []
            for pickup, delivery in removed_pairs:  # iterate every pair
                costs = []
                for vehicle_id, route in enumerate(self.solution.routes):  # iterate every route
                    min_cost = float('inf')
                    temp_solution = deepcopy(self.solution)
                    for i in range(1, len(route)):
                        for j in range(i, len(route)):
                            temp_route = route[:i] + [pickup] + route[i:j] + [delivery] + route[j:]
                            # temp_solution = deepcopy(self.solution)
                            temp_solution.routes[vehicle_id] = temp_route
                            temp_solution.update_all()

                            if temp_solution.is_feasible():
                                cost = temp_solution.objective_function()
                                if cost < min_cost:
                                    min_cost = cost
                                    best_i, best_j = i, j

                    if min_cost < float('inf'):
                        costs.append((min_cost, vehicle_id, best_i, best_j))
                costs.sort(key=lambda x: x[0])
                insertion_costs.append((pickup, delivery, costs))

            best_request = None
            best_route = None
            best_insert_position = None
            for pickup, delivery, costs in insertion_costs:
                # 无法被插入到任何路径，直接跳过
                if len(costs) == 0:
                    removed_pairs.remove((pickup, delivery))
                    # print(f"Request ({pickup}, {delivery}) cannot be inserted into any route.")
                    continue
                # 处理插入机会少于k的请求
                elif len(costs) > 0 and len(costs) < k:
                    best_request = (pickup, delivery)
                    best_route = costs[0][1]
                    best_insert_position = (costs[0][2], costs[0][3])
                    break
                # 如果没有插入机会少于k的请求，则选择最大遗憾值的请求
                elif len(costs) >= k:
                    max_regret = float('-inf')
                    regret = sum(cost[0] for cost in costs[:k]) - costs[0][0]
                    if regret > max_regret:
                        max_regret = regret
                        best_request = (pickup, delivery)
                        best_route = costs[0][1]
                        best_insert_position = (costs[0][2], costs[0][3])

                        # 插入最佳请求
            if best_request is not None and best_route is not None and best_insert_position is not None:
                removed_pairs.remove(best_request)
                pickup, delivery = best_request
                self.insert_single_request(pickup, delivery, best_route, best_insert_position)

        return self.solution

    # *****************************************************************************************************
    # End of regret insertion
    def insert_single_request(self, pickup, delivery, vehicle_id, insert_position):
        i, j = insert_position
        self.solution.routes[vehicle_id] = self.solution.routes[vehicle_id][:i] \
                                           + [pickup] + self.solution.routes[vehicle_id][i:j] + [delivery] \
                                           + self.solution.routes[vehicle_id][j:]
        self.solution.update_all()  # update all of the things
        self.record_insertion(vehicle_id, pickup, delivery, insert_position)  # 记录插入位置

    def record_insertion(self, vehicle_id, pickup, delivery, position):
        """
        记录插入位置
        vehicle_id: 车辆ID
        pickup: 取货点
        delivery: 送货点
        position: 插入位置 (i, j)
        """
        self.insertion_log.append({
            'vehicle_id': vehicle_id,
            'pickup': pickup,
            'delivery': delivery,
            'position': position
        })

    def get_insertion_log(self):
        """
        获取插入日志
        :return: 插入日志
        """
        return self.insertion_log

