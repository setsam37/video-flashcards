import {render,screen} from '@testing-library/react';
import {expect,test} from 'vitest';
import {ImportPanel} from './ImportPanel';

test('free online import offers YouTube and explains local video uploads',()=>{
 render(<ImportPanel onImported={()=>{}} videoUploadsEnabled={false}/>);
 expect(screen.getByRole('button',{name:'YouTube link'})).toBeInTheDocument();
 expect(screen.queryByRole('button',{name:'Upload video'})).not.toBeInTheDocument();
 expect(screen.getByText(/Use the local app for video uploads/)).toBeInTheDocument();
});

test('local import retains uploaded video option',()=>{
 render(<ImportPanel onImported={()=>{}} videoUploadsEnabled/>);
 expect(screen.getByRole('button',{name:'Upload video'})).toBeInTheDocument();
});
