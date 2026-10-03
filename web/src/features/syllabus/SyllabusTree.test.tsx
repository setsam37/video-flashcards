import {render,screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {expect,test,vi} from 'vitest';
import {SyllabusTree} from './SyllabusTree';
const nodes=[{id:'p',title:'Parent chapter',start:0,end:600,parent_id:null,inferred:false},{id:'c',title:'Relevant subtopic',start:120,end:240,parent_id:'p',inferred:true}];
test('chapter selection returns the full interval',async()=>{
 const change=vi.fn();render(<SyllabusTree nodes={nodes} selected={[]} onChange={change} cardCounts={{}}/>);
 await userEvent.click(screen.getByRole('checkbox',{name:'Parent chapter'}));
 expect(change).toHaveBeenCalledWith([{start:0,end:600}]);
 expect(screen.queryByText(/\d+ cards/)).not.toBeInTheDocument();
});
test('a partially selected parent has an indeterminate checkbox',()=>{
 render(<SyllabusTree nodes={nodes} selected={[{start:120,end:240}]} onChange={()=>{}} cardCounts={{c:2,p:2}}/>);
 expect(screen.getByRole('checkbox',{name:'Parent chapter'})).toBePartiallyChecked();
 expect(screen.getByRole('checkbox',{name:'Relevant subtopic'})).toBeChecked();
});
