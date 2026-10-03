"""Explicit real-provider check; does not generate new cards automatically."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from app.config import Config
from app.storage import Repository
from app.providers.openai_provider import OpenAIProvider
from app.models import Interval,CardCandidate

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--lecture-id',required=True)
    parser.add_argument('--interval',nargs=2,type=float,required=True,metavar=('START','END'))
    args=parser.parse_args();span=Interval(start=args.interval[0],end=args.interval[1]);config=Config()
    repo=Repository(config.data_dir/'study.sqlite');view=repo.get_lecture(args.lecture_id)
    segments={s.id:s for s in repo.get_segments(args.lecture_id)};provider=OpenAIProvider(config)
    cards=[c for c in view.cards if span.start<=c.primary_time<span.end]
    if not cards:raise SystemExit('No generated cards in that interval. Generate the selected material in the app first.')
    for card in cards:
        candidate=CardCandidate(**{k:getattr(card,k) for k in ['point_ids','front','back','source_segment_ids']},primary_segment_id=next(id for id in card.source_segment_ids if segments[id].start==card.primary_time))
        supported=provider.check_support(candidate,[segments[id] for id in card.source_segment_ids])
        print(json.dumps({'card_id':card.id,'primary_time':card.primary_time,'source_ids':card.source_segment_ids,'supported':supported}))
        if not supported:raise SystemExit('A card failed the live support check.')
    print(f'Live evidence check passed for {len(cards)} cards.')
if __name__=='__main__':main()
