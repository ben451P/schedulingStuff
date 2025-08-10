
            # if prev_availability != availability:
            #     for i in range(len(availability)):
                    
            #         if not availability[i] and prev_availability[i]:
            #             new_state[new_state.index(i)] = -1
            #     for i in range(len(availability)):
            #         if availability[i] and not prev_availability[i]:
            #             if -1 in new_state:
            #                 new_state[new_state.index(-1)] = i
                                    
            # if num_avail > prev_num_avail:
            #     for guard_num in range(len(availability)):
            #         if availability[guard_num] and guard_num not in new_state:
            #             new_state.append(guard_num)

            # elif num_avail < prev_num_avail:
            #     while -1 in new_state:
            #         index = new_state.index(-1)
            #         temp = new_state[index]
            #         new_state[index] = new_state[-1]
            #         new_state.pop(-1)
            # print(new_state)