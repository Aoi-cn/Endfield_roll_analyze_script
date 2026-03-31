import random

# UP角色中文名列表
UP_NAMES = ['1_莱', '2_洁', '3_伊冯', '4_汤汤', '5_洛希']

def get_off_rate_pool(pool_idx):
    """
    获取当前卡池歪角色的卡池名单
    规则：5个常驻6星 + 前两期的UP角色 (开服前两个池子特殊处理)
    """
    standard = ['常驻_S1', '常驻_S2', '常驻_S3', '常驻_S4', '常驻_S5']
    if pool_idx == 0:
        return standard + [UP_NAMES[1], UP_NAMES[2]]  # 第1个池子（索引0）可歪 UP_1, UP_2
    elif pool_idx == 1:
        return standard + [UP_NAMES[0], UP_NAMES[2]]  # 第2个池子（索引1）可歪 UP_0, UP_2
    elif pool_idx == 2:
        return standard + [UP_NAMES[0], UP_NAMES[1]]  # 第3个池子（索引2）可歪 UP_0, UP_1
    else:
        return standard + [UP_NAMES[pool_idx-1], UP_NAMES[pool_idx-2]]

def simulate_gacha(pulls_per_pool, wanted_characters, num_players):
    """
    模拟四种策略下玩家获得角色的概率分布、抽数消耗及六星数量
    """
    # 策略定义:
    # 1: 想要的抽到出, 不想要的【完全不抽】(0抽)
    # 2: 想要的抽到出, 不想要/已有的【续到30抽】(拿免费10连)
    # 3: 想要的抽到出, 不想要/已有的【续到60抽】(拿免费10连+下期10连券)
    # 4: 不管想不想要，每个池子【固定投入60抽】
    
    results = {}
    
    for strategy in range(1, 5):
        char_counts = {}
        combo_counts = {}
        total_remaining_currency = 0
        total_spent_pulls_all_players = 0  # 统计该策略下所有玩家的总投入抽数
        total_std_6_count = 0  # 统计该策略下所有玩家获得的常驻六星总数
        total_all_6_count = 0  # 统计该策略下所有玩家获得的总六星数量
        
        for _ in range(num_players):
            inventory = set()
            player_spent_pulls = 0   # 记录当前玩家总投入抽数（含赠送）
            player_std_6_count = 0   # 记录当前玩家获得的常驻六星数量
            player_total_6_count = 0  # 记录当前玩家获得的总六星数量
            pity_6_star = 0
            currency = 0
            next_pool_tickets = 0
            
            for pool_idx, pool_pulls_gained in enumerate(pulls_per_pool):
                # 领取本期资源和上期留下的券
                currency += pool_pulls_gained
                currency += next_pool_tickets
                next_pool_tickets = 0
                
                want_this = (wanted_characters[pool_idx] == 1)
                pool_pulls = 0
                up_name = UP_NAMES[pool_idx]
                
                while currency > 0:
                    has_up = (up_name in inventory)
                    stop = False
                    
                    # 停止条件判断
                    if strategy == 4:
                        if pool_pulls >= 60: stop = True
                    else:
                        if want_this and not has_up:
                            pass # 想要且还没拿到，继续抽
                        else:
                            # 不想要，或者已经拿到了，判断是否触发策略续抽
                            if strategy == 1: stop = True
                            elif strategy == 2:
                                if pool_pulls >= 30: stop = True
                            elif strategy == 3:
                                if pool_pulls >= 60: stop = True
                                
                    if stop: break
                        
                    # 执行一次基础抽取
                    currency -= 1
                    pool_pulls += 1
                    player_spent_pulls += 1 # 投入抽数+1
                    pity_6_star += 1
                    
                    # 概率计算 (65抽开始递增，80抽硬保底)
                    prob = 0.008
                    if pity_6_star >= 65:
                        prob = 0.008 + (pity_6_star - 64) * 0.05
                    if pity_6_star >= 80:
                        prob = 1.0
                        
                    # 判定出货
                    if random.random() < prob:
                        pity_6_star = 0  # 保底清零
                        player_total_6_count += 1
                        if random.random() < 0.5:
                            inventory.add(up_name)
                        else:
                            off_pool = get_off_rate_pool(pool_idx)
                            dropped_char = random.choice(off_pool)
                            inventory.add(dropped_char)
                            if dropped_char.startswith('常驻_'):
                                player_std_6_count += 1
                            
                    # 120抽硬保底 (定向必得当期UP)
                    if pool_pulls == 120:
                        if up_name not in inventory:
                            player_total_6_count += 1
                        inventory.add(up_name)
                        
                    # 30抽额外里程碑：送10连（不计入保底，但计入总抽数）
                    if pool_pulls == 30:
                        player_spent_pulls += 10 # 获赠的10抽也算在“抽了多少抽”里
                        for _ in range(10):
                            if random.random() < 0.008: 
                                player_total_6_count += 1
                                if random.random() < 0.5:
                                    inventory.add(up_name)
                                else:
                                    off_pool = get_off_rate_pool(pool_idx)
                                    dropped_char = random.choice(off_pool)
                                    inventory.add(dropped_char)
                                    if dropped_char.startswith('常驻_'):
                                        player_std_6_count += 1
                                    
                    # 60抽额外里程碑：送下期10连券
                    if pool_pulls == 60:
                        next_pool_tickets += 10
            
            # 汇总该玩家数据
            total_remaining_currency += currency
            total_spent_pulls_all_players += player_spent_pulls
            total_std_6_count += player_std_6_count
            total_all_6_count += player_total_6_count
            
            for char in inventory:
                char_counts[char] = char_counts.get(char, 0) + 1
            
            up_combo = tuple(sorted([char for char in inventory if char in UP_NAMES]))
            combo_counts[up_combo] = combo_counts.get(up_combo, 0) + 1
            
        # 计算各项平均值
        stats = {char: count / num_players for char, count in char_counts.items()}
        combos = {combo: count / num_players for combo, count in combo_counts.items()}
        
        results[f"策略 {strategy}"] = {
            'avg_currency': total_remaining_currency / num_players,
            'avg_spent_pulls': total_spent_pulls_all_players / num_players, # 平均总投入
            'avg_std_6_stars': total_std_6_count / num_players,
            'avg_total_6_stars': total_all_6_count / num_players,
            'individual': stats,
            'combos': combos
        }
    return results

# ================= 模拟运行 =================
if __name__ == "__main__":
    # 输入参数：5个池子，初始/过程获得的资源
    pulls_per_pool = [100, 60, 60, 60, 60] 
    wanted_characters = [1, 1, 1, 1, 1]
    num_players = 100000

    print(f"正在模拟 {num_players} 名玩家的抽卡结果...")
    res = simulate_gacha(pulls_per_pool, wanted_characters, num_players)
    
    for strat, data in res.items():
        print(f"\n=== {strat} ===")
        print(f"平均总投入抽数 (含赠送): {data['avg_spent_pulls']:.2f}")
        print(f"平均剩余抽数 (资源存量): {data['avg_currency']:.2f}")
        print(f"平均获得总六星数量: {data['avg_total_6_stars']:.2f}")
        print(f"平均获得常驻六星数量: {data['avg_std_6_stars']:.2f}")
        
        print("各UP角色持有率:")
        for up_name in UP_NAMES:
            prob = data['individual'].get(up_name, 0)
            print(f"  [{up_name}]: {prob:.2%}")

        print("常见UP组合分布 (概率 > 2%):")
        sorted_combos = sorted(data['combos'].items(), key=lambda x: x[1], reverse=True)
        for combo, prob in sorted_combos:
            if prob > 0.02:
                combo_str = " + ".join(combo) if combo else "无UP"
                print(f"  [{combo_str}]: {prob:.2%}")
