# KAGGRICULTURE AGENT - DIRDIRI-3 (Minimal Working Version)
# Author: Dr.EldirdiriFadol

from typing import Dict, Any

# Simple state tracking
_state = None

def agent(obs: Dict[str, Any]) -> Dict[str, Any]:
    global _state
    
    # Initialize state
    if _state is None:
        _state = {
            'day': 0,
            'hour': 0,
            'hired_today': 0,
            'phase': 'EARLY'
        }
    
    # Update state
    _state['day'] = obs['day']
    _state['hour'] = obs['hour']
    
    # Reset hired count at start of day
    if _state['hour'] == 0:
        _state['hired_today'] = 0
    
    # Determine phase
    if _state['day'] < 10:
        _state['phase'] = 'EARLY'
    elif _state['day'] < 20:
        _state['phase'] = 'MID'
    else:
        _state['phase'] = 'LATE'
    
    # Get player info
    player = obs['player']
    me = obs['farms'][player]
    private = obs['private']
    market = obs['market']
    
    # Get position
    fx, fy = me['farmer']
    tiles = me['tiles']
    money = me['money']
    
    farmer_actions = []
    market_actions = []
    hand_actions = []
    
    # Get shed inventory
    shed_items = private.get('shed', {})
    seeds = private.get('seeds', {})
    
    # ----- SELL ITEMS -----
    for item, count in shed_items.items():
        if count > 0:
            price = market['prices'].get(item, 0)
            base_prices = {
                'WHEAT': 25, 'CARROT': 35, 'TOMATO': 60,
                'STRAWBERRY': 120, 'MELON': 250,
                'EGG': 50, 'MILK': 160, 'WOOL': 200,
                'FERTILIZER': 100
            }
            base = base_prices.get(item, 50)
            
            # Sell if price is good or we have too many
            if price > base or count > 10:
                market_actions.append(['SELL', item, count])
    
    # ----- BUY SEEDS -----
    # Priority crops based on phase
    if _state['phase'] == 'EARLY':
        crops = ['WHEAT', 'CARROT']
    elif _state['phase'] == 'MID':
        crops = ['TOMATO', 'WHEAT']
    else:
        crops = ['TOMATO', 'GOOSE']
    
    for crop in crops[:2]:
        if seeds.get(crop, 0) < 3:
            cost = {'WHEAT': 10, 'CARROT': 20, 'TOMATO': 50, 
                   'STRAWBERRY': 100, 'MELON': 80}.get(crop, 50)
            if money > cost * 3:
                market_actions.append(['BUY_SEED', crop, 3 - seeds.get(crop, 0)])
    
    # ----- BUY WHEAT FOR FEED -----
    if shed_items.get('WHEAT', 0) < 10 and money > 50:
        market_actions.append(['BUY_PRODUCT', 'WHEAT', 5])
    
    # ----- HIRE -----
    if _state['hired_today'] < 2 and money > 100:
        market_actions.append(['HIRE'])
        _state['hired_today'] += 1
    
    # ----- BUY LAND -----
    unlocked = me.get('unlocked_quadrants', [])
    if len(unlocked) < 4:
        cost = [1000, 2000, 4000][len(unlocked)]
        if money > cost + 200:
            market_actions.append(['BUY_LAND'])
    
    # ----- FARMER ACTIONS -----
    current_tile = None
    if 0 <= fy < len(tiles) and 0 <= fx < len(tiles[fy]):
        current_tile = tiles[fy][fx]
    
    # Handle Animals
    if current_tile and isinstance(current_tile, dict):
        kind = current_tile.get('kind')
        
        # COOP or PASTURE
        if kind in ['COOP', 'PASTURE']:
            if current_tile.get('animal'):
                # Care if not cared today
                if not current_tile.get('cared_today', False):
                    farmer_actions.append('CARE')
                    return {'farmer': farmer_actions, 'hands': hand_actions, 'market': market_actions}
                
                # Harvest if has yield
                if current_tile.get('yield_units', 0) > 0:
                    farmer_actions.append('HARVEST')
                    return {'farmer': farmer_actions, 'hands': hand_actions, 'market': market_actions}
                
                # Collect fertilizer
                if current_tile.get('fertilizer_available', False):
                    farmer_actions.append('COLLECT_FERTILIZER')
                    return {'farmer': farmer_actions, 'hands': hand_actions, 'market': market_actions}
        
        # Handle Plants
        if kind == 'PLANT':
            # Water if needed
            if not current_tile.get('watered_today', False):
                farmer_actions.append('WATER')
                return {'farmer': farmer_actions, 'hands': hand_actions, 'market': market_actions}
            
            # Harvest if ready
            if current_tile.get('yield_units', 0) > 0:
                farmer_actions.append('HARVEST')
                return {'farmer': farmer_actions, 'hands': hand_actions, 'market': market_actions}
        
        # Clear weeds
        if kind == 'WEED':
            farmer_actions.append('DIG')
            return {'farmer': farmer_actions, 'hands': hand_actions, 'market': market_actions}
    
    # Plant new crops on empty tile
    if current_tile is None:
        # Check if we have any seeds
        for crop in crops:
            if seeds.get(crop, 0) > 0:
                farmer_actions.append('PLANT')
                return {'farmer': farmer_actions, 'hands': hand_actions, 'market': market_actions}
    
    # Build structures for animals
    if current_tile is None:
        if shed_items.get('GOOSE', 0) > 0:
            farmer_actions.append('BUILD_COOP')
            return {'farmer': farmer_actions, 'hands': hand_actions, 'market': market_actions}
    
    # ----- MOVE TO FIND WORK -----
    # Find plants needing water
    for y, row in enumerate(tiles):
        for x, tile in enumerate(row):
            if tile is None or tile == 'LOCKED':
                continue
            if isinstance(tile, dict):
                # Plant needs water
                if tile.get('kind') == 'PLANT' and not tile.get('watered_today', False):
                    if x > fx:
                        farmer_actions.append('EAST')
                    elif x < fx:
                        farmer_actions.append('WEST')
                    elif y > fy:
                        farmer_actions.append('SOUTH')
                    elif y < fy:
                        farmer_actions.append('NORTH')
                    return {'farmer': farmer_actions, 'hands': hand_actions, 'market': market_actions}
                
                # Animal needs care
                if tile.get('kind') in ['COOP', 'PASTURE']:
                    if tile.get('animal') and not tile.get('cared_today', False):
                        if x > fx:
                            farmer_actions.append('EAST')
                        elif x < fx:
                            farmer_actions.append('WEST')
                        elif y > fy:
                            farmer_actions.append('SOUTH')
                        elif y < fy:
                            farmer_actions.append('NORTH')
                        return {'farmer': farmer_actions, 'hands': hand_actions, 'market': market_actions}
                
                # Plant ready to harvest
                if tile.get('kind') == 'PLANT' and tile.get('yield_units', 0) > 0:
                    if x > fx:
                        farmer_actions.append('EAST')
                    elif x < fx:
                        farmer_actions.append('WEST')
                    elif y > fy:
                        farmer_actions.append('SOUTH')
                    elif y < fy:
                        farmer_actions.append('NORTH')
                    return {'farmer': farmer_actions, 'hands': hand_actions, 'market': market_actions}
    
    # Find empty tile to move to
    for y, row in enumerate(tiles):
        for x, tile in enumerate(row):
            if tile is None:
                if x > fx:
                    farmer_actions.append('EAST')
                elif x < fx:
                    farmer_actions.append('WEST')
                elif y > fy:
                    farmer_actions.append('SOUTH')
                elif y < fy:
                    farmer_actions.append('NORTH')
                return {'farmer': farmer_actions, 'hands': hand_actions, 'market': market_actions}
    
    # Default: go to shed
    if fx != 0 or fy != 0:
        if fx > 0:
            farmer_actions.append('WEST')
        elif fy > 0:
            farmer_actions.append('NORTH')
    else:
        farmer_actions.append('PASS')
    
    return {'farmer': farmer_actions, 'hands': hand_actions, 'market': market_actions}