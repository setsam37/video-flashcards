import {render,screen} from '@testing-library/react';
import {expect,test,vi} from 'vitest';
import App from './App';
test('a prepared syllabus has no automatic flashcards and empty selection disables generation',async()=>{
 const lesson={id:'lesson',title:'Test lecture',duration:600,source_kind:'youtube',youtube_id:'C842vFY5kRo',media_url:null,syllabus:[{id:'p',title:'Actual chapter',start:0,end:600,parent_id:null,inferred:false}],cards:[],gaps:[],completed_intervals:[],jobs:[]};
 vi.stubGlobal('fetch',async(input:RequestInfo|URL)=>new Response(JSON.stringify(String(input).endsWith('/health')?{status:'ok',provider_configured:true}:String(input).endsWith('/lectures')?[{id:'lesson',title:'Test lecture',duration:600}]:lesson),{status:200,headers:{'Content-Type':'application/json'}}));
 render(<App/>);
 expect(await screen.findByRole('checkbox',{name:'Actual chapter'})).toBeInTheDocument();
 expect(screen.getByRole('button',{name:'Generate flashcards'})).toBeDisabled();
 expect(screen.getByText('No cards generated yet')).toBeInTheDocument();
 vi.unstubAllGlobals();
});
