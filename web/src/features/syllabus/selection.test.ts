import {expect,test} from 'vitest';
import {normalizeIntervals,subtractIntervals,toggleNode} from './selection';
test('children alone exclude the intervening chapter material',()=>expect(normalizeIntervals([{start:120,end:240},{start:360,end:480}])).toEqual([{start:120,end:240},{start:360,end:480}]));
test('unchecking a child preserves the rest of its chapter',()=>expect(subtractIntervals([{start:0,end:600}],[{start:120,end:240}])).toEqual([{start:0,end:120},{start:240,end:600}]));
test('overlapping selections are represented once',()=>expect(normalizeIntervals([{start:0,end:300},{start:120,end:500}])).toEqual([{start:0,end:500}]));
test('selecting a parent includes its full interval',()=>expect(toggleNode([], {id:'p',title:'Parent',start:0,end:600,parent_id:null,inferred:false},true)).toEqual([{start:0,end:600}]));
