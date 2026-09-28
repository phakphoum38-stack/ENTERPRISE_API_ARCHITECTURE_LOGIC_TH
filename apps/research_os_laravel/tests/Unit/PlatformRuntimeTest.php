<?php
declare(strict_types=1);
namespace Tests\Unit;
use PHPUnit\Framework\TestCase;
use ResearchOS\Platform\Contracts\RequestContext;
use ResearchOS\Platform\Infrastructure\ConfiguredVersionGateway;
final class PlatformRuntimeTest extends TestCase {
    public function test_version_gateway_is_fail_closed_for_unknown_major(): void {
        $gateway=new ConfiguredVersionGateway('1');
        $this->assertTrue($gateway->supports('1.0.0'));
        $this->assertFalse($gateway->supports('2.0.0'));
        $this->assertFalse($gateway->supports('UNKNOWN'));
    }
    public function test_request_context_is_explicit(): void {
        $context=new RequestContext('r','c','a','1.0.0');
        $this->assertSame('r',$context->requestId);
        $this->assertSame('c',$context->correlationId);
    }
}
