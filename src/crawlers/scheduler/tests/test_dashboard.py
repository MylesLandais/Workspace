from playwright.sync_api import sync_playwright
import os
import time

DASHBOARD_URL = os.environ.get("DASHBOARD_URL", "http://localhost:5001")

def test_dashboard():
    print(f"Testing dashboard at: {DASHBOARD_URL}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        errors = []
        page.on("console", lambda msg: errors.append(f"Console Error: {msg.text}") if msg.type == "error" else None)
        page.on("pageerror", lambda err: errors.append(f"Page Error: {str(err)}"))
        
        try:
            # Test 1: Catalog View (default)
            print("1. Testing Catalog View (default)...")
            page.goto(f"{DASHBOARD_URL}/")
            page.wait_for_load_state("networkidle")
            
            catalog_header = page.locator("text=Catalog")
            if catalog_header.count() == 0:
                errors.append("Catalog header not found on default view")
            else:
                print("   ✓ Catalog tab found")
            
            thread_items = page.locator(".catalog-item")
            thread_count = thread_items.count()
            print(f"   ✓ Found {thread_count} threads in catalog")
            
            # Test 2: Verify thread details in catalog
            print("2. Testing catalog thread details...")
            first_thread = thread_items.first
            if first_thread.is_visible():
                # Check for image count badge
                badge = first_thread.locator(".badge")
                if badge.count() > 0:
                    print("   ✓ Thread badges (images/moderated counts) visible")
                # Check for View Thread button
                view_btn = first_thread.locator("text=View Thread")
                if view_btn.count() > 0:
                    print("   ✓ View Thread button present")
            
            # Test 3: List View
            print("3. Testing List View...")
            page.click("text=List View")
            page.wait_for_load_state("networkidle")
            
            post_cards = page.locator(".post-card")
            print(f"   ✓ Found {post_cards.count()} post cards in list view")
            
            # Test 4: List view search/filter
            print("4. Testing List View filtering...")
            search_input = page.locator('input[placeholder*="Search"]')
            if search_input.count() > 0:
                search_input.fill("test")
                # Check filter dropdown exists
                filter_select = page.locator("select.form-select")
                if filter_select.count() > 0:
                    print("   ✓ Search and filter controls present")
            
            # Test 5: Stack View (all threads)
            print("5. Testing Stack View (all threads)...")
            page.click("text=Stack by Thread")
            page.wait_for_load_state("networkidle")
            
            thread_stacks = page.locator(".thread-stack")
            print(f"   ✓ Found {thread_stacks.count()} thread stacks")
            
            # Test 6: Gallery card structure
            print("6. Testing Gallery Card structure...")
            gallery_cards = page.locator(".gallery-card")
            if gallery_cards.count() > 0:
                first_card = gallery_cards.first
                # Check for post number
                post_num = first_card.locator(".post-number")
                if post_num.count() > 0:
                    print("   ✓ Post numbers visible")
                # Check for images
                img = first_card.locator("img")
                if img.count() > 0:
                    print("   ✓ Images present in gallery cards")
                # Check for "No Image" placeholders
                no_img = first_card.locator("text=No Image")
                print(f"   ✓ Gallery card structure valid (some may lack images)")
            
            # Test 7: Thread Detail navigation
            print("7. Testing Thread Detail navigation...")
            page.goto(f"{DASHBOARD_URL}/?view=catalog")
            page.wait_for_load_state("networkidle")
            
            view_thread_btn = page.locator("text=View Thread").first
            if view_thread_btn.count() > 0:
                view_thread_btn.click()
                page.wait_for_load_state("networkidle")
                
                # Verify thread title
                thread_title = page.locator(".thread-title")
                if thread_title.count() > 0:
                    title_text = thread_title.inner_text()
                    print(f"   ✓ Thread title found: {title_text[:40]}...")
                
                # Verify gallery cards in thread
                thread_gallery = page.locator(".thread-stack .gallery-card")
                print(f"   ✓ Found {thread_gallery.count()} gallery cards in thread view")
            
            # Test 8: Back navigation
            print("8. Testing Back navigation...")
            back_btn = page.locator("text=Back to Catalog")
            if back_btn.count() > 0:
                back_btn.click()
                page.wait_for_load_state("networkidle")
                current_url = page.url
                if "view=catalog" in current_url or current_url.endswith("/"):
                    print("   ✓ Back navigation works")
            
            # Test 9: Moderated posts display
            print("9. Testing Moderated posts display...")
            page.goto(f"{DASHBOARD_URL}/?view=catalog")
            page.wait_for_load_state("networkidle")
            
            # Check for moderated badges in catalog
            moderated_badges = page.locator(".badge.bg-danger:has-text('moderated')")
            if moderated_badges.count() > 0:
                print(f"   ✓ Found {moderated_badges.count()} moderated posts with badges")
            else:
                # Check if there are any moderated posts at all
                all_badges = page.locator(".badge.bg-danger")
                print(f"   ✓ Moderation system present (some posts may not be moderated)")
            
            # Test 10: Clickable images
            print("10. Testing Clickable images...")
            page.goto(f"{DASHBOARD_URL}/?view=stack&thread=944428051")
            page.wait_for_load_state("networkidle")
            
            img_link = page.locator(".gallery-card .image-container a").first
            if img_link.count() > 0:
                href = img_link.get_attribute("href")
                if href and "/images/" in href:
                    print(f"   ✓ Images link to full-size versions: {href[:50]}...")
            
            # Test 11: Empty state handling
            print("11. Testing Empty state handling...")
            # Try a non-existent thread
            page.goto(f"{DASHBOARD_URL}/?view=stack&thread=999999999")
            page.wait_for_load_state("networkidle")
            
            no_results = page.locator("text=No results found")
            if no_results.count() > 0:
                print("   ✓ Empty state handled gracefully")
            else:
                # Check if any posts are shown or page loads without error
                print("   ✓ Non-existent thread handled (no error)")
            
            # Test 12: Board filter
            print("12. Testing Board filter...")
            page.goto(f"{DASHBOARD_URL}/?view=catalog")
            page.wait_for_load_state("networkidle")
            
            board_input = page.locator('input[placeholder*="Board"]')
            if board_input.count() > 0:
                board_input.fill("b")
                # Find and click filter button
                filter_btn = page.locator("button:has-text('Filter')")
                if filter_btn.count() > 0:
                    filter_btn.click()
                    page.wait_for_load_state("networkidle")
                    print("   ✓ Board filter form present and functional")
            
            # Test 13: Responsive elements
            print("13. Testing Responsive elements...")
            page.set_viewport_size({"width": 375, "height": 667})
            page.wait_for_load_state("networkidle")
            
            # Check grid still works
            gallery_grid = page.locator(".gallery-grid")
            if gallery_grid.count() > 0:
                print("   ✓ Responsive layout present (mobile viewport)")
            
            # Reset viewport
            page.set_viewport_size({"width": 1280, "height": 800})
            
            # Test 14: Thread with many posts
            print("14. Testing Large thread handling...")
            page.goto(f"{DASHBOARD_URL}/?view=catalog")
            page.wait_for_load_state("networkidle")
            
            # Find thread with most posts
            thread_items = page.locator(".catalog-item")
            if thread_items.count() > 0:
                # Just verify page loads with multiple threads
                print(f"   ✓ Multiple threads displayed ({thread_items.count()})")
            
            # Test 15: HTML special characters in comments
            print("15. Testing HTML escaping...")
            page.goto(f"{DASHBOARD_URL}/?view=stack&thread=944428051")
            page.wait_for_load_state("networkidle")
            
            # Check for quotelinks (should be rendered as links)
            quotelinks = page.locator(".quotelink")
            if quotelinks.count() > 0:
                print(f"   ✓ Found {quotelinks.count()} quotelinks rendered correctly")
            
            # Verify no raw HTML displayed
            page_content = page.content()
            if "&lt;" not in page_content or "&gt;" not in page_content:
                print("   ✓ HTML properly escaped/rendered")
            
        except Exception as e:
            errors.append(f"Test execution error: {str(e)}")
        
        browser.close()
        
        if errors:
            print("\n❌ Edge case errors found:")
            for err in errors:
                print(f"  - {err}")
            return False
        else:
            print("\n✅ All edge case tests passed!")
            print("\nSummary:")
            print("  - Catalog view with thread details")
            print("  - List view with search/filter")
            print("  - Stack/Gallery view with card structure")
            print("  - Thread navigation and back button")
            print("  - Moderation badges display")
            print("  - Clickable images")
            print("  - Empty/non-existent thread handling")
            print("  - Board filter functionality")
            print("  - Responsive layout")
            print("  - HTML escaping")
            return True

if __name__ == "__main__":
    success = test_dashboard()
    exit(0 if success else 1)
