import {render,screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {expect,test,vi} from 'vitest';
import {PagesEntry} from './PagesEntry';

test('Pages clearly explains that submitting a video cannot generate a lesson without its server',async()=>{
 const fetchSpy=vi.spyOn(globalThis,'fetch');
 render(<PagesEntry appUrl=""/>);
 const field=screen.getByRole('textbox',{name:'Paste your video link'});
 expect(field).toHaveValue('');
 await userEvent.type(field,'https://www.youtube.com/watch?v=C842vFY5kRo');
 await userEvent.click(screen.getByRole('button',{name:'Proceed to lesson'}));
 expect(await screen.findByRole('alert')).toHaveTextContent('Video processing is not connected');
 expect(fetchSpy).not.toHaveBeenCalled();
 fetchSpy.mockRestore();
});

test('an unsupported video link is rejected before the handoff',async()=>{
 render(<PagesEntry appUrl=""/>);
 await userEvent.type(screen.getByRole('textbox',{name:'Paste your video link'}),'https://example.com/video');
 await userEvent.click(screen.getByRole('button',{name:'Proceed to lesson'}));
 expect(await screen.findByRole('alert')).toHaveTextContent('YouTube');
});

test('a connected entry submits the video directly to the processing server',()=>{
 render(<PagesEntry appUrl="https://recall.example"/>);
 const field=screen.getByRole('textbox',{name:'Paste your video link'});
 expect(field).toHaveAttribute('name','url');
 expect(field.closest('form')).toHaveAttribute('method','post');
 expect(field.closest('form')).toHaveAttribute('action','https://recall.example/start');
 expect(screen.getByText('Sign in with Google to save this lesson in your private library.')).toBeInTheDocument();
});
