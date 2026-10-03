import {render,screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {expect,test,vi} from 'vitest';
import {PagesEntry} from './PagesEntry';

test('Pages clearly explains that submitting a video cannot generate a lesson without its server',async()=>{
 const fetchSpy=vi.spyOn(globalThis,'fetch');
 render(<PagesEntry/>);
 const field=screen.getByRole('textbox',{name:'Paste your video link'});
 expect(field).toHaveValue('');
 await userEvent.type(field,'https://www.youtube.com/watch?v=C842vFY5kRo');
 await userEvent.click(screen.getByRole('button',{name:'Proceed to lesson'}));
 expect(await screen.findByRole('alert')).toHaveTextContent('Video processing is not connected');
 expect(fetchSpy).not.toHaveBeenCalled();
 fetchSpy.mockRestore();
});

test('an unsupported video link is rejected before the handoff',async()=>{
 render(<PagesEntry/>);
 await userEvent.type(screen.getByRole('textbox',{name:'Paste your video link'}),'https://example.com/video');
 await userEvent.click(screen.getByRole('button',{name:'Proceed to lesson'}));
 expect(await screen.findByRole('alert')).toHaveTextContent('YouTube');
});
