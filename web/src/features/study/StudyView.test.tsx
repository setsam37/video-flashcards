import {render,screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {test,expect,vi} from 'vitest';
import {useState} from 'react';
import {StudyView} from './StudyView';
import type {Card,LectureView} from '../../types';
import type {StudySession} from './session';
const cards:Card[]=[{id:'a',lecture_id:'lesson',topic_id:'p',point_ids:['x'],front:'What is balancing?',back:'Distributing requests.',primary_time:16,source_start:16,source_end:20,source_segment_ids:['s1'],source_excerpt:'The instructor distributes requests.'},{id:'b',lecture_id:'lesson',topic_id:'p',point_ids:['y'],front:'Second question?',back:'Second answer.',primary_time:25,source_start:25,source_end:30,source_segment_ids:['s2'],source_excerpt:'Second evidence.'}];
const lecture={id:'lesson',title:'Test lecture',youtube_id:'C842vFY5kRo',media_url:null,syllabus:[{id:'p',title:'Balancing',start:0,end:300,parent_id:null,inferred:false}]} as LectureView;
function Harness(){const [session,setSession]=useState<StudySession>({cardIds:['a','b'],index:0,flipped:false});return <StudyView session={session} cards={cards} lecture={lecture} onSessionChange={setSession} onExit={()=>{}}/>;}
test('flipping reveals the answer and navigating resets the question side',async()=>{
 render(<Harness/>);await userEvent.click(screen.getByRole('button',{name:'Flip card'}));
 expect(screen.getByText('Distributing requests.')).toBeVisible();
 expect(screen.getByRole('link',{name:'Watch this explanation'})).toHaveAttribute('href','https://www.youtube.com/watch?v=C842vFY5kRo&t=16s');
 await userEvent.click(screen.getByRole('button',{name:'Next card'}));
 expect(screen.getByText('Second question?')).toBeVisible();
 expect(screen.queryByText('Second answer.')).not.toBeInTheDocument();
});
test('keyboard Space flips and the source link does not flip the card',async()=>{
 render(<Harness/>);screen.getByRole('button',{name:'Flip card'}).focus();await userEvent.keyboard(' ');
 expect(screen.getByText('Distributing requests.')).toBeVisible();
 await userEvent.click(screen.getByRole('link',{name:'Watch this explanation'}));
 expect(screen.getByText('Distributing requests.')).toBeVisible();
});
