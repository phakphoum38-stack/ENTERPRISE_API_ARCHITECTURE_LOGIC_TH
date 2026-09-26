from pathlib import Path
import json
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'current/RESEARCH_OS_AUTHORIZATION_CONVERGENCE_CONTRACT.json'
def main():
    d=json.loads(DATA.read_text(encoding='utf-8'))
    assert d['status']=='ACTIVE'
    assert d['owner']['role']=='OWNER'
    assert d['owner']['resource_or_scope_bound'] is False
    assert d['authorization']['flutter_may_grant'] is False
    assert d['authorization']['flutter_may_authorize'] is False
    print('IDENTITY_ACCESS_CONVERGENCE=PASS')
if __name__=='__main__': main()
