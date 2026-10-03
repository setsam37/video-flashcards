import {test,expect} from 'vitest';
import {createSession,reconcileSession} from './session';
import type {Card} from '../../types';
const card=(id:string,time:number):Card=>({id,lecture_id:'test',topic_id:'chapter',point_ids:['p'],front:'Question',back:'Answer',primary_time:time,source_start:time,source_end:time+1,source_segment_ids:['s'],source_excerpt:'Evidence'});
const cards=[card('later',310),card('first',10),card('child',130),card('child',130)];
test('one-topic includes descendant timestamps in lecture order',()=>expect(createSession(cards,'topic',[{start:0,end:300}],false).cardIds).toEqual(['first','child']));
test('custom mixing includes only eligible unique cards',()=>expect(createSession(cards,'custom',[{start:120,end:240}],true).cardIds).toEqual(['child']));
test('whole mixing preserves eligible membership',()=>expect([...createSession(cards,'all',[],true).cardIds].sort()).toEqual(['child','first','later']));
test('removed cards are reconciled without losing the current surviving card',()=>expect(reconcileSession({cardIds:['first','child','later'],index:1,flipped:true},[card('child',130),card('later',310)])).toEqual({cardIds:['child','later'],index:0,flipped:true}));
