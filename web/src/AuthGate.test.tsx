import {render,screen,waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {afterEach,expect,test,vi} from 'vitest';
import {AuthGate} from './AuthGate';
afterEach(()=>vi.unstubAllGlobals());

test('signed out visitors see Google sign in and no private content',async()=>{
 vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:true,json:async()=>({hosted:true,authenticated:false})}));
 render(<AuthGate>{()=> <p>Private lesson</p>}</AuthGate>);
 expect(await screen.findByRole('link',{name:'Continue with Google'})).toHaveAttribute('href','/auth/login');
 expect(screen.queryByText('Private lesson')).not.toBeInTheDocument();
});

test('the pasted lesson is consumed with CSRF before opening the library',async()=>{
 const fetch=vi.fn().mockResolvedValueOnce({ok:true,json:async()=>({hosted:true,authenticated:true,email:'owner@example.test',csrf_token:'csrf-test',pending:true})}).mockResolvedValueOnce({ok:true,json:async()=>({lecture_id:'new-lecture',job_id:'job'})});
 vi.stubGlobal('fetch',fetch);
 render(<AuthGate>{()=> <p>Private lesson</p>}</AuthGate>);
 expect(await screen.findByText('Private lesson')).toBeInTheDocument();
 expect(fetch.mock.calls[1][0]).toBe('/api/handoff');
 expect(new Headers(fetch.mock.calls[1][1].headers).get('X-CSRF-Token')).toBe('csrf-test');
 expect(sessionStorage.getItem('recall-active-lecture')).toBe('new-lecture');
});

test('signing out removes private content and clears cached study state',async()=>{
 const fetch=vi.fn().mockResolvedValueOnce({ok:true,json:async()=>({hosted:true,authenticated:true,email:'owner@example.test',csrf_token:'csrf-test'})}).mockResolvedValueOnce({ok:true,json:async()=>({signed_out:true})});
 vi.stubGlobal('fetch',fetch);sessionStorage.setItem('recall-session-lecture','private');
 render(<AuthGate>{()=> <p>Private lesson</p>}</AuthGate>);
 await userEvent.click(await screen.findByRole('button',{name:'Sign out'}));
 await waitFor(()=>expect(screen.queryByText('Private lesson')).not.toBeInTheDocument());
 expect(sessionStorage.getItem('recall-session-lecture')).toBeNull();
});
