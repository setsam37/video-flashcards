import {render,screen} from '@testing-library/react';
import {beforeEach,expect,test,vi} from 'vitest';
import App from './App';
beforeEach(()=>sessionStorage.clear());
test('a prepared syllabus has no automatic flashcards and empty selection disables generation',async()=>{
 const lesson={id:'lesson',title:'Test lecture',duration:600,source_kind:'youtube',youtube_id:'C842vFY5kRo',media_url:null,syllabus:[{id:'p',title:'Actual chapter',start:0,end:600,parent_id:null,inferred:false}],cards:[],gaps:[],completed_intervals:[],jobs:[]};
 vi.stubGlobal('fetch',async(input:RequestInfo|URL)=>new Response(JSON.stringify(String(input).endsWith('/health')?{status:'ok',provider_configured:true}:String(input).endsWith('/lectures')?[{id:'lesson',title:'Test lecture',duration:600}]:lesson),{status:200,headers:{'Content-Type':'application/json'}}));
 render(<App/>);
 expect(await screen.findByRole('checkbox',{name:'Actual chapter'})).toBeInTheDocument();
 expect(screen.getByRole('button',{name:'Generate flashcards'})).toBeDisabled();
 expect(screen.getByText('No cards generated yet')).toBeInTheDocument();
 vi.unstubAllGlobals();
});

test('reload restores the active older lecture and its current answer',async()=>{
 const base={duration:600,source_kind:'youtube',youtube_id:'C842vFY5kRo',media_url:null,syllabus:[],gaps:[],completed_intervals:[],jobs:[]};
 const cards=[0,1].map(index=>({id:'old-card-'+index,lecture_id:'older',topic_id:'topic',point_ids:['point'],front:'Old question '+index,back:'Old answer '+index,primary_time:index*10,source_start:index*10,source_end:index*10+5,source_segment_ids:['segment'],source_excerpt:'Old evidence'}));
 const old={...base,id:'older',title:'Older lecture',cards};
 const recent={...base,id:'recent',title:'Recent lecture',cards:[]};
 sessionStorage.setItem('recall-active-lecture','older');
 sessionStorage.setItem('recall-session-older',JSON.stringify({cardIds:cards.map(c=>c.id),index:1,flipped:true}));
 vi.stubGlobal('fetch',async(input:RequestInfo|URL)=>new Response(JSON.stringify(String(input).endsWith('/health')?{status:'ok',provider_configured:true}:String(input).endsWith('/lectures')?[{id:'recent',title:recent.title,duration:600},{id:'older',title:old.title,duration:600}]:String(input).endsWith('/older')?old:recent),{status:200,headers:{'Content-Type':'application/json'}}));
 render(<App/>);
 expect(await screen.findByText('2 of 2 cards')).toBeInTheDocument();
 expect(screen.getByRole('heading',{name:'Older lecture'})).toBeInTheDocument();
 expect(screen.getByRole('button',{name:'Show question'})).toHaveTextContent('Old answer 1');
 vi.unstubAllGlobals();
});
